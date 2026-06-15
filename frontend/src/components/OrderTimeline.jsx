const STEPS = [
  { key: 'paid',             label: 'Order Confirmed'  },
  { key: 'packed',           label: 'Packed'           },
  { key: 'shipped',          label: 'Shipped'          },
  { key: 'out_for_delivery', label: 'Out for Delivery' },
  { key: 'delivered',        label: 'Delivered'        },
]

const TERMINAL = {
  cancelled: { label: 'This order has been cancelled.', cls: 'timeline-banner--cancelled' },
  returned:  { label: 'This order has been returned.',  cls: 'timeline-banner--returned'  },
  refunded:  { label: 'Refund has been processed.',     cls: 'timeline-banner--refunded'  },
}

function fmt(isoStr) {
  if (!isoStr) return ''
  return new Date(isoStr).toLocaleString('en-IN', {
    day: 'numeric', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit', hour12: true,
  })
}

export default function OrderTimeline({ statusHistory = [], currentStatus, courierName, trackingNumber }) {
  const isTerminal     = currentStatus in TERMINAL
  const currentStepIdx = STEPS.findIndex(s => s.key === currentStatus)

  const histMap = {}
  for (const entry of statusHistory) {
    histMap[entry.status] = entry
  }

  return (
    <div className="order-timeline">
      {isTerminal && (
        <div className={`timeline-banner ${TERMINAL[currentStatus].cls}`}>
          {TERMINAL[currentStatus].label}
        </div>
      )}

      <div className="timeline-steps">
        {STEPS.map((step, idx) => {
          const hist = histMap[step.key]
          let state  = 'pending'
          if (isTerminal) {
            state = hist ? 'done' : 'pending'
          } else {
            if      (idx < currentStepIdx)  state = 'done'
            else if (idx === currentStepIdx) state = 'active'
          }

          return (
            <div key={step.key} className={`timeline-step timeline-step--${state}`}>
              <div className="timeline-dot">
                {state === 'done' ? '✓' : state === 'active' ? '●' : '○'}
              </div>
              <div className="timeline-content">
                <div className="timeline-label">{step.label}</div>
                {hist && (
                  <div className="timeline-meta">
                    <span className="timeline-date">{fmt(hist.at)}</span>
                    {hist.note && <span className="timeline-note">{hist.note}</span>}
                  </div>
                )}
                {step.key === 'shipped' && state !== 'pending' && (courierName || trackingNumber) && (
                  <div className="timeline-courier">
                    {courierName    && <span>📦 {courierName}</span>}
                    {trackingNumber && <span>Tracking: {trackingNumber}</span>}
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
