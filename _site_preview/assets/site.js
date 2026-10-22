/* Shared navigation for the static site. No third-party runtime is required. */
(function () {
  "use strict";

  function onReady() {
    const body = document.body;
    const header = document.querySelector(".main-header.main-header-original");
    const desktopQuery = window.matchMedia("(min-width: 980px)");
    const reducedMotionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");

    if (header) {
      const toggle = header.querySelector(".drawer-hamburger");
      const drawer = header.querySelector(".drawer-navigation");
      const overlay = header.querySelector(".drawer-overlay");

      // Leave the document's ordinary links available if the enhanced menu
      // cannot be initialized. CSS must only collapse them after this succeeds.
      if (toggle && drawer && overlay) {
        const focusableSelector = [
          "a[href]",
          "area[href]",
          "button:not([disabled])",
          "input:not([disabled]):not([type='hidden'])",
          "select:not([disabled])",
          "textarea:not([disabled])",
          "[tabindex]:not([tabindex='-1'])"
        ].join(",");
        let isOpen = false;
        let returnFocus = toggle;

        if (!drawer.id) {
          let id = "site-drawer-navigation";
          let suffix = 1;
          while (document.getElementById(id)) {
            suffix += 1;
            id = "site-drawer-navigation-" + suffix;
          }
          drawer.id = id;
        }
        toggle.type = "button";
        toggle.setAttribute("aria-controls", drawer.id);
        toggle.setAttribute("aria-expanded", "false");
        drawer.setAttribute("tabindex", "-1");
        overlay.setAttribute("aria-hidden", "true");

        function isFocusable(element) {
          return element instanceof HTMLElement &&
            !element.hasAttribute("disabled") &&
            element.tabIndex >= 0 &&
            element.getClientRects().length > 0 &&
            window.getComputedStyle(element).visibility !== "hidden";
        }

        function focusWithoutScrolling(element) {
          if (element instanceof HTMLElement && element.isConnected) {
            element.focus({ preventScroll: true });
          }
        }

        function menuFocusables() {
          // The toggle is also the close control and remains part of the
          // keyboard sequence while the drawer covers the page.
          return [toggle].concat(Array.from(drawer.querySelectorAll(focusableSelector)))
            .filter(isFocusable);
        }

        function closeMenu(restoreFocus) {
          const wasOpen = isOpen;
          isOpen = false;
          body.classList.remove("drawer-open");
          toggle.setAttribute("aria-expanded", "false");
          drawer.hidden = true;
          overlay.hidden = true;
          if (wasOpen && restoreFocus && !desktopQuery.matches) {
            focusWithoutScrolling(isFocusable(returnFocus) ? returnFocus : toggle);
          }
        }

        function openMenu() {
          if (desktopQuery.matches || isOpen) {
            return;
          }
          returnFocus = document.activeElement instanceof HTMLElement
            ? document.activeElement : toggle;
          isOpen = true;
          drawer.hidden = false;
          overlay.hidden = false;
          toggle.setAttribute("aria-expanded", "true");
          body.classList.add("drawer-open");
          const firstLink = Array.from(drawer.querySelectorAll(focusableSelector))
            .find(isFocusable);
          focusWithoutScrolling(firstLink || drawer);
        }

        function resetForViewport() {
          const activeElement = document.activeElement;
          const desktopNavigation = header.querySelector(
            ".main-header-content .main-navigation"
          );
          const menuHadFocus = activeElement === toggle || drawer.contains(activeElement) ||
            (!desktopQuery.matches && desktopNavigation &&
              desktopNavigation.contains(activeElement));
          const activeHref = activeElement instanceof HTMLAnchorElement
            ? activeElement.href : null;
          closeMenu(false);
          toggle.hidden = desktopQuery.matches;
          if (menuHadFocus) {
            if (desktopQuery.matches) {
              const desktopLinks = Array.from(header.querySelectorAll(
                ".main-header-content .main-navigation a[href]"
              ));
              const destination = desktopLinks.find(function (link) {
                return activeHref && link.href === activeHref;
              }) || desktopLinks.find(isFocusable);
              focusWithoutScrolling(destination);
            } else {
              focusWithoutScrolling(toggle);
            }
          }
        }

        toggle.addEventListener("click", function () {
          if (isOpen) {
            closeMenu(true);
          } else {
            openMenu();
          }
        });

        overlay.addEventListener("click", function () {
          closeMenu(true);
        });

        drawer.addEventListener("click", function (event) {
          const target = event.target instanceof Element ? event.target : null;
          if (target && target.closest("a[href]")) {
            // Preserve the browser's normal link, hash, and new-tab behavior.
            closeMenu(true);
          }
        });

        document.addEventListener("click", function (event) {
          const target = event.target;
          if (isOpen && target instanceof Node &&
              !drawer.contains(target) && !toggle.contains(target)) {
            closeMenu(true);
          }
        });

        document.addEventListener("keydown", function (event) {
          if (!isOpen) {
            return;
          }
          if (event.key === "Escape") {
            event.preventDefault();
            closeMenu(true);
            return;
          }
          if (event.key !== "Tab") {
            return;
          }
          const items = menuFocusables();
          if (!items.length) {
            event.preventDefault();
            focusWithoutScrolling(drawer);
            return;
          }
          const first = items[0];
          const last = items[items.length - 1];
          const active = document.activeElement;
          if (event.shiftKey && (active === first || !items.includes(active))) {
            event.preventDefault();
            focusWithoutScrolling(last);
          } else if (!event.shiftKey && (active === last || !items.includes(active))) {
            event.preventDefault();
            focusWithoutScrolling(first);
          }
        });

        if (typeof desktopQuery.addEventListener === "function") {
          desktopQuery.addEventListener("change", resetForViewport);
        } else {
          desktopQuery.addListener(resetForViewport);
        }

        body.classList.add("navigation-ready");
        resetForViewport();
      }
    }

    const backToTop = document.querySelector("button.back-to-top");
    if (backToTop) {
      let framePending = false;
      backToTop.type = "button";

      function updateBackToTop() {
        backToTop.hidden = window.scrollY <= 300;
        framePending = false;
      }

      window.addEventListener("scroll", function () {
        if (!framePending) {
          framePending = true;
          window.requestAnimationFrame(updateBackToTop);
        }
      }, { passive: true });

      backToTop.addEventListener("click", function () {
        const titleLink = document.querySelector(".site-branding .site-title a");
        if (titleLink instanceof HTMLElement) {
          titleLink.focus({ preventScroll: true });
        }
        window.scrollTo({
          top: 0,
          behavior: reducedMotionQuery.matches ? "auto" : "smooth"
        });
      });

      updateBackToTop();
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", onReady, { once: true });
  } else {
    onReady();
  }
}());
\n\n(function () {\n  "use strict";\n  function b(v){return String(v).toLowerCase()==="true";}\n  function init(){document.querySelectorAll("[data-achievement-filter]").forEach(function(bar){\n    var root=bar.closest(".entry-content")||document, kind=bar.dataset.filterKind;\n    var buttons=Array.from(bar.querySelectorAll("button[data-filter-value]"));\n    var items=Array.from(root.querySelectorAll("[data-achievement-item]"));\n    var lists=Array.from(root.querySelectorAll("[data-achievement-list]"));\n    var empty=root.querySelector("[data-achievement-empty]");\n    function match(item,v){if(v==="all")return true;if(kind==="presentation")return item.dataset.scope===v;var f=b(item.dataset.first),c=b(item.dataset.corresponding);return v==="first"?f:v==="first-or-corresponding"?(f||c):true;}\n    function apply(v){var visible=[];items.forEach(function(i){i.hidden=!match(i,v);if(!i.hidden)visible.push(i);});visible.forEach(function(i,n){i.value=visible.length-n;});lists.forEach(function(l){var show=Array.from(l.querySelectorAll("[data-achievement-item]")).some(function(i){return !i.hidden;});l.hidden=!show;var h=l.previousElementSibling;if(h&&h.classList.contains("achievement-year-heading"))h.hidden=!show;});buttons.forEach(function(x){var a=x.dataset.filterValue===v;x.classList.toggle("is-active",a);x.setAttribute("aria-pressed",a?"true":"false");});if(empty)empty.hidden=visible.length!==0;}\n    buttons.forEach(function(x){x.addEventListener("click",function(){apply(x.dataset.filterValue||"all");});var n=items.filter(function(i){return match(i,x.dataset.filterValue||"all");}).length;var c=x.querySelector("[data-filter-count]");if(c)c.textContent="("+n+")";});apply("all");\n  });}\n  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init,{once:true});else init();\n}());\n