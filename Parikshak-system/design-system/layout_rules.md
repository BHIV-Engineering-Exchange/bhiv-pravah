# BHIV Command Center Design System — Layout Rules

To ensure a true command-center feeling and avoid unnecessary vertical scrolling, pages must use grid layout partitions designed to fit within the viewport height.

## Grid Rules

### Desktop (Viewport width >= 1024px)
- **Dashboard**: 3-column or 4-column structured grid. Main metric cards form a top hero row.
- **Review result details**: Left 2/3 column holds technical code metrics, repository, and task description. Right 1/3 column contains recommendation results, deliverables check, and evidence logs.
- **Console views**: Side-by-side splits with sticky metadata columns and scrollable code details.

### Tablet (Viewport width >= 768px and < 1024px)
- **Niyantran assignment**: Tablet-first! Multi-row layout splits: Top summary panel, middle workflow allocation panel (Assignee, workload match %, override selectors), bottom timeline audit panel.

### Mobile (Viewport width < 768px)
- Linearized flex layouts with collapsible section cards.
- Bottom floating action buttons or tab bar navigation.
- Hide dense JSON snippets behind a toggle/modal to prevent screen height bloat.
