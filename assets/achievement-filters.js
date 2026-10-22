(() => {
  const groups = document.querySelectorAll('[data-achievement-filter]');

  groups.forEach((group) => {
    const list = document.getElementById(group.dataset.target);
    if (!list) return;

    const items = Array.from(list.querySelectorAll(':scope > li'));
    const buttons = Array.from(group.querySelectorAll('[data-filter-value]'));
    const status = document.getElementById(`${list.id.replace('-list', '')}-filter-status`);

    const matches = (item, value) =>
      (item.dataset.filters || 'all').split(/\s+/).includes(value);

    const updateCounts = () => {
      buttons.forEach((button) => {
        const value = button.dataset.filterValue;
        const count = items.filter((item) => matches(item, value)).length;
        const target = button.querySelector(`[data-filter-count="${value}"]`);
        if (target) target.textContent = `(${count})`;
      });
    };

    const applyFilter = (value) => {
      const visible = [];
      items.forEach((item) => {
        const show = matches(item, value);
        item.hidden = !show;
        if (show) visible.push(item);
      });
      if (list.hasAttribute('reversed')) {
        visible.forEach((item, index) => {
          item.value = visible.length - index;
        });
      }
      buttons.forEach((button) => {
        button.setAttribute('aria-pressed', String(button.dataset.filterValue === value));
      });
      if (status) status.textContent = `${visible.length}件を表示しています。`;
    };

    updateCounts();
    buttons.forEach((button) => {
      button.addEventListener('click', () => applyFilter(button.dataset.filterValue));
    });
    applyFilter('all');
  });
})();
