
const tabs = {};
const form = document.getElementById('form');

const navTabs = document.getElementById('navTabs');
const radios = navTabs.querySelectorAll('input[type=radio]');

radios.forEach(radioBtn => {
    
    const option = radioBtn.id;
    const groupName = radioBtn.name;
    const isChecked = radioBtn.checked;

    const tab = form.querySelector(`#${option}`);
    
    tabs[groupName] ??= {
        elements: [],
        current: undefined
    };
    tabs[groupName].elements.push(tab);

    if (isChecked) {
        tabs[groupName].current = tab;
    }

    radioBtn.addEventListener('click', (e)=>{

        tabs[groupName].current?.removeAttribute('checked');
        
        tabs[groupName].current = tab;
        tabs[groupName].current?.setAttribute('checked', true);
    });
});

window.tabs = tabs;