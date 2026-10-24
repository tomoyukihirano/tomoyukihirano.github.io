(() => {
  'use strict';
  const views = new Map([...document.querySelectorAll('[data-site-view]')].map(view => [view.dataset.siteView, view]));
  const labels = {home:'Home',about:'About',research:'Research',publications:'Publications',presentations:'Presentations',grants:'Grants',award:'Award'};
  let current = 'home';
  const navToggle = document.getElementById('nav-toggle');
  const siteNav = document.getElementById('site-nav');
  function closeNavigation() {
    siteNav.classList.remove('is-open');
    navToggle.setAttribute('aria-expanded','false');
  }
  navToggle.addEventListener('click',() => {
    const open = navToggle.getAttribute('aria-expanded') !== 'true';
    navToggle.setAttribute('aria-expanded',String(open));
    siteNav.classList.toggle('is-open',open);
  });
  document.addEventListener('keydown',event => {
    if (event.key === 'Escape' && navToggle.getAttribute('aria-expanded') === 'true') {
      closeNavigation();navToggle.focus();
    }
  });

  function anchorPage() {
    const id = location.hash.slice(1);
    if (/^(pub-\d+|review-\d+|preprint-|year-|reviews$|preprints$|book-chapters-3-in-total$|others$)/.test(id)) return 'publications';
    if (/^(pres-\d+|pr-year-\d+|presentations-page$)/.test(id)) return 'presentations';
    if (id.startsWith('view-') && views.has(id.slice(5))) return id.slice(5);
    return null;
  }
  function show(page, {push = false, focus = false, anchor = ''} = {}) {
    if (!views.has(page)) page = 'home';
    current = page;
    document.body.dataset.page = page;
    closeNavigation();
    views.forEach((view,key) => {view.hidden = key !== page;});
    document.querySelectorAll('.header-inner nav [data-site-page]').forEach(link => {
      if (link.dataset.sitePage === page) link.setAttribute('aria-current','page');
      else link.removeAttribute('aria-current');
    });
    document.title = `${labels[page]} · Tomoyuki Hirano`;
    if (push) {
      try {
        const url = new URL(location.href);
        url.searchParams.set('page',page);
        url.hash = anchor;
        history.pushState({page},'',url.href);
      } catch (_) { /* Navigation remains usable when local files restrict history. */ }
    }
    if (page === 'presentations') window.initializePresentationPreview?.();
    if (focus) {
      const title = views.get(page).querySelector('h1');
      if (title) { title.tabIndex = -1; title.focus({preventScroll:true}); }
      window.scrollTo({top:0,behavior:'auto'});
    }
    if (anchor) requestAnimationFrame(() => {
      let id;
      try {id = decodeURIComponent(anchor.replace(/^#/,''));} catch (_) {return;}
      const target = document.getElementById(id);
      if (target && views.get(page).contains(target)) target.scrollIntoView({block:'start',behavior:'auto'});
    });
    if (page === 'publications' && location.hash) window.revealPublicationAnchor?.();
  }
  function read() {
    const page = anchorPage() || new URLSearchParams(location.search).get('page') || 'home';
    show(page,{anchor:location.hash});
  }
  document.addEventListener('click',event => {
    const link = event.target.closest('a[data-site-page]');
    if (!link || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    const next = link.dataset.sitePage;
    const anchor = new URL(link.href,location.href).hash;
    show(next,{push:true,focus:next !== current,anchor});
  });
  window.addEventListener('popstate',read);
  window.addEventListener('hashchange',() => {
    const page = anchorPage();
    if (page && page !== current) show(page,{anchor:location.hash});
  });
  read();
})();
