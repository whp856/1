/**
 * HMS 医院管理系统 - 全局交互脚本
 */
document.addEventListener('DOMContentLoaded', function() {
    initMessages();
    initKeyboardShortcuts();
});

function initMessages() {
    var msgs = document.querySelectorAll('.msg');
    msgs.forEach(function(msg) {
        setTimeout(function() {
            msg.style.transition = 'opacity 0.3s';
            msg.style.opacity = '0';
            setTimeout(function() { if (msg.parentNode) msg.remove(); }, 300);
        }, 4000);
    });
}

function initKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') {
            return;
        }
        if (e.ctrlKey && e.key === 's') {
            e.preventDefault();
            var form = document.querySelector('form');
            if (form) form.submit();
        }
        if (e.key === 'Escape') {
            var searchResults = document.querySelectorAll('.search-results');
            searchResults.forEach(function(el) { el.style.display = 'none'; });
        }
    });
}

function toggleSidebar() {
    var sidebar = document.getElementById('sidebar');
    if (sidebar) {
        sidebar.classList.toggle('open');
    }
}

function confirmAction(msg) {
    return confirm(msg || '确认执行此操作?');
}
