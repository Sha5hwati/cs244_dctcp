/* Modified DCTCP for Noisy Environments (1% Loss / 200us Jitter) */

#include <linux/module.h>
#include <linux/mm.h>
#include <net/tcp.h>
#include <linux/inet_diag.h>
#include "improved_dctcp.h"

#define DCTCP_MAX_ALPHA	1024U

struct dctcp {
	u32 old_delivered;
	u32 old_delivered_ce;
	u32 prior_rcv_nxt;
	u32 dctcp_alpha;
	u32 next_seq;
	u32 ce_state;
	u32 loss_cwnd;
};

/* Increased g to 6 to smooth out jitter */
static unsigned int dctcp_shift_g __read_mostly = 6; 
module_param(dctcp_shift_g, uint, 0644);
MODULE_PARM_DESC(dctcp_shift_g, "parameter g for updating dctcp_alpha");

static unsigned int dctcp_alpha_on_init __read_mostly = DCTCP_MAX_ALPHA;
module_param(dctcp_alpha_on_init, uint, 0644);

static struct tcp_congestion_ops dctcp_reno;

static void dctcp_reset(const struct tcp_sock *tp, struct dctcp *ca)
{
	ca->next_seq = tp->snd_nxt;
	ca->old_delivered = tp->delivered;
	ca->old_delivered_ce = tp->delivered_ce;
}

static void dctcp_init(struct sock *sk)
{
	const struct tcp_sock *tp = tcp_sk(sk);
	if ((tp->ecn_flags & TCP_ECN_OK) ||
	    (sk->sk_state == TCP_LISTEN ||
	     sk->sk_state == TCP_CLOSE)) {
		struct dctcp *ca = inet_csk_ca(sk);
		ca->prior_rcv_nxt = tp->rcv_nxt;
		ca->dctcp_alpha = min(dctcp_alpha_on_init, DCTCP_MAX_ALPHA);
		ca->loss_cwnd = 0;
		ca->ce_state = 0;
		dctcp_reset(tp, ca);
		return;
	}
	inet_csk(sk)->icsk_ca_ops = &dctcp_reno;
	INET_ECN_dontxmit(sk);
}

static u32 dctcp_ssthresh(struct sock *sk)
{
	struct dctcp *ca = inet_csk_ca(sk);
	struct tcp_sock *tp = tcp_sk(sk);
	ca->loss_cwnd = tp->snd_cwnd;
    
	return max(tp->snd_cwnd - ((tp->snd_cwnd * ca->dctcp_alpha) >> 11U), 2U);
}

static void dctcp_update_alpha(struct sock *sk, u32 flags)
{
	const struct tcp_sock *tp = tcp_sk(sk);
	struct dctcp *ca = inet_csk_ca(sk);

	if (!before(tp->snd_una, ca->next_seq)) {
		u32 delivered_ce = tp->delivered_ce - ca->old_delivered_ce;
		u32 alpha = ca->dctcp_alpha;

		alpha -= min_not_zero(alpha, alpha >> dctcp_shift_g);
		if (delivered_ce) {
			u32 delivered = tp->delivered - ca->old_delivered;
			delivered_ce <<= (10 - dctcp_shift_g);
			delivered_ce /= max(1U, delivered);
			alpha = min(alpha + delivered_ce, DCTCP_MAX_ALPHA);
		}
		WRITE_ONCE(ca->dctcp_alpha, alpha);
		dctcp_reset(tp, ca);
	}
}

static void dctcp_react_to_loss(struct sock *sk)
{
    struct dctcp *ca = inet_csk_ca(sk);
    struct tcp_sock *tp = tcp_sk(sk);
    ca->loss_cwnd = tp->snd_cwnd;

    /* If alpha is <5%, only reduce congestion window by 1/8. If alpha is greater,
	try to use standard DCTCP reduction instead of Reno. */
    if (ca->dctcp_alpha < 50) { 
        tp->snd_ssthresh = max(tp->snd_cwnd - (tp->snd_cwnd >> 4U), 2U); 
    } else {
        u32 reduction = (tp->snd_cwnd * ca->dctcp_alpha) >> 11U;
        tp->snd_ssthresh = max(tp->snd_cwnd - reduction, 2U);
    }
}

static void dctcp_state(struct sock *sk, u8 new_state)
{
	if (new_state == TCP_CA_Recovery &&
	    new_state != inet_csk(sk)->icsk_ca_state)
		dctcp_react_to_loss(sk);
}

static void dctcp_cwnd_event(struct sock *sk, enum tcp_ca_event ev)
{
	struct dctcp *ca = inet_csk_ca(sk);
	switch (ev) {
	case CA_EVENT_ECN_IS_CE:
	case CA_EVENT_ECN_NO_CE:
		dctcp_ece_ack_update(sk, ev, &ca->prior_rcv_nxt, &ca->ce_state);
		break;
	case CA_EVENT_LOSS:
		dctcp_react_to_loss(sk);
		break;
	default:
		break;
	}
}

static size_t dctcp_get_info(struct sock *sk, u32 ext, int *attr,
			     union tcp_cc_info *info)
{
	const struct dctcp *ca = inet_csk_ca(sk);
	const struct tcp_sock *tp = tcp_sk(sk);
	/* Fill it also in case of VEGASINFO due to req struct limits.
	 * We can still correctly retrieve it later.
	 */
	if (ext & (1 << (INET_DIAG_DCTCPINFO - 1)) ||
	    ext & (1 << (INET_DIAG_VEGASINFO - 1))) {
		memset(&info->dctcp, 0, sizeof(info->dctcp));
		if (inet_csk(sk)->icsk_ca_ops != &dctcp_reno) {
			info->dctcp.dctcp_enabled = 1;
			info->dctcp.dctcp_ce_state = (u16) ca->ce_state;
			info->dctcp.dctcp_alpha = ca->dctcp_alpha;
			info->dctcp.dctcp_ab_ecn = tp->mss_cache *
						   (tp->delivered_ce - ca->old_delivered_ce);
			info->dctcp.dctcp_ab_tot = tp->mss_cache *
						   (tp->delivered - ca->old_delivered);
		}
		*attr = INET_DIAG_DCTCPINFO;
		return sizeof(info->dctcp);
	}
	return 0;
}

static u32 dctcp_cwnd_undo(struct sock *sk)
{
	const struct dctcp *ca = inet_csk_ca(sk);
	return max(tcp_sk(sk)->snd_cwnd, ca->loss_cwnd);
}

static struct tcp_congestion_ops dctcp __read_mostly = {
	.init		= dctcp_init,
	.in_ack_event   = dctcp_update_alpha,
	.cwnd_event	= dctcp_cwnd_event,
	.ssthresh	= dctcp_ssthresh,
	.cong_avoid	= tcp_reno_cong_avoid,
	.undo_cwnd	= dctcp_cwnd_undo,
	.set_state	= dctcp_state,
	.owner		= THIS_MODULE,
	.name		= "dctcp_v4",
};

static struct tcp_congestion_ops dctcp_reno __read_mostly = {
	.ssthresh	= tcp_reno_ssthresh,
	.cong_avoid	= tcp_reno_cong_avoid,
	.undo_cwnd	= tcp_reno_undo_cwnd,
	.get_info	= dctcp_get_info,
	.owner		= THIS_MODULE,
	.name		= "dctcp-reno",
};
static int __init dctcp_register(void)
{
	BUILD_BUG_ON(sizeof(struct dctcp) > ICSK_CA_PRIV_SIZE);
	return tcp_register_congestion_control(&dctcp);
}
static void __exit dctcp_unregister(void)
{
	tcp_unregister_congestion_control(&dctcp);
}
module_init(dctcp_register);
module_exit(dctcp_unregister);
MODULE_AUTHOR("Alisha Nanda <alishan@stanford.edu>");
MODULE_AUTHOR("Shashwati Shraddha <shaswatis@stanford.edu>");
MODULE_LICENSE("GPL v2");
MODULE_DESCRIPTION("DataCenter TCP with Improvements (DCTCP)");
