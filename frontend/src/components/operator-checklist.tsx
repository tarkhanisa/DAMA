import type { OperatorChecklistItem } from "../lib/operator-workflow";

type OperatorChecklistProps = {
  items: OperatorChecklistItem[];
  nextAction: OperatorChecklistItem;
};

function stateLabel(state: OperatorChecklistItem["state"]): string {
  if (state === "done") {
    return "انجام شده";
  }

  if (state === "active") {
    return "قدم فعلی";
  }

  if (state === "warning") {
    return "نیازمند بررسی";
  }

  return "بعداً";
}

export function OperatorChecklist({ items, nextAction }: OperatorChecklistProps) {
  return (
    <section className="operator-checklist-panel">
      <div className="next-action-card">
        <div>
          <p className="eyebrow">قدم بعدی پیشنهادی</p>
          <h2>{nextAction.title}</h2>
          <p>{nextAction.description}</p>
        </div>

        <a href={nextAction.href}>{nextAction.actionLabel}</a>
      </div>

      <div className="operator-checklist">
        {items.map((item) => (
          <a
            key={item.step}
            className={`checklist-item checklist-${item.state}`}
            href={item.href}
          >
            <span className="checklist-step">{item.step}</span>
            <div>
              <strong>{item.title}</strong>
              <p>{item.description}</p>
            </div>
            <em>{stateLabel(item.state)}</em>
          </a>
        ))}
      </div>
    </section>
  );
}
