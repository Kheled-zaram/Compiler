function processorDependantTab(selectedId) {
    const selectedForm = document.getElementById('dependant_tab_' + selectedId);
    const forms_div = document.getElementById('tab4_forms')
    const msg = document.getElementById('dependant_msg')
    let dependantTabs = document.querySelectorAll('[id^="dependant_tab_"]');

    for (let tab of dependantTabs) {
        tab.style.display = "none";
    }
    selectedForm.style.display = "block";
    msg.style.display = "none";
    forms_div.style.display = "block";
}

function clickHandle(evt, tabName) {
    let i, tabContent, tablinks;

    // This is to clear the previous clicked content.
    tabContent = document.getElementsByClassName("tab-content");
    for (i = 0; i < tabContent.length; i++) {
        tabContent[i].style.display = "none";
    }

    // Set the tab to be "active".
    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }

    document.getElementById(tabName).style.display = "block";
    evt.currentTarget.className += " active";
}

window.addEventListener('load', () => {
    const theme = localStorage.getItem('theme');
    if (theme === 'dark') {
        darkMode();
    }
})


function darkMode(evt) {
    document.documentElement.classList.toggle("dark-theme");
    document.getElementById("dark").style.display = "none";
    document.getElementById("light").style.display = "block";
    localStorage.setItem('theme', 'dark');
}

function lightMode(evt) {
    document.documentElement.classList.toggle("dark-theme");
    document.getElementById("dark").style.display = "block";
    document.getElementById("light").style.display = "none";
    localStorage.setItem('theme', 'light');
}


function highlightAsm(subsection) {
    const subsection2 = getSecondSubsectionAsm(subsection)

    if (subsection.id.includes("header")) {

        subsection.classList.add("asm-header-highlight");
        subsection2.classList.add("asm-content-highlight");
    } else {
        subsection2.classList.add("asm-header-highlight");
        subsection.classList.add("asm-content-highlight");
    }
}

function unhighlightAsm(subsection) {
    const subsection2 = getSecondSubsectionAsm(subsection)
    subsection.classList.remove("asm-header-highlight");
    subsection2.classList.remove("asm-content-highlight");
    subsection2.classList.remove("asm-header-highlight");
    subsection.classList.remove("asm-content-highlight");
}

function getSecondSubsectionAsm(subsection) {
    if (subsection.id.includes("header"))
        return document.getElementById(subsection.id.replace("header", "content"));
    return document.getElementById(subsection.id.replace("content", "header"));
}
