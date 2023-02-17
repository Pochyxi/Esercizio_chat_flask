const scrollToBottom = (id) => {
    const element = document.getElementById(id);
    element.scrollTop = element.scrollHeight;
}

let to_scroll = document.getElementById('to_scroll')
to_scroll.scrollTop = to_scroll.scrollHeight * 2

