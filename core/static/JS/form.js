
const sendButton = document.getElementById("sendButton");
const resetButton = document.getElementById("resetButton");


//#region On Buttons Clicked

sendButton.addEventListener('click', (e)=>{

    makeAction({

        onPresets: sendPresets,
        onCustomParams: sendCustomParams
    });
});

resetButton.addEventListener('click', (e)=>{

    makeAction({

        onPresets: clearPresets,
        onCustomParams: clearCustomParams
    });
});

//#endregion


function makeAction(callbackHandler) {

    const currentTab = window.tabs['options-form-tabs']?.current.id;

    switch(currentTab) {

        case 'presets':
            return callbackHandler?.onPresets();
            
        case 'customParams':
            return callbackHandler?.onCustomParams();

        default:
            return null;
    }
}


//#region Send Data

async function sendPresets () {

    const presetId = window.cards['options-presets'].current?.id; 

    if (presetId) {

        const url = `${window.location.origin}/preset/${presetId}`;
        
        const response = await fetch(url);
        const json = await response.json();

        console.log(json);

        //todo draw chart.js
    }
    else {

        //todo send warning
        return null;
    }
}

async function sendCustomParams() {

    const url = `${window.location.origin}/params`;
    
    const body = {
        name: "test",
        price: "10"
    };

    const options = {
        method: 'post',
        body: JSON.stringify(body),
        headers: {
            'Content-Type': 'application/json',
        },
    };

    const response = await fetch(url, options);

    const json = await response.json();

    console.log(json);
}

//#endregion


//#region Clear Infut Fields

function clearPresets() {
    window.cards['options-presets'].current?.removeAttribute('checked');
    window.cards['options-presets'].current = null;
}

function clearCustomParams() {
    alert("todo: clear custom params!");
}

//#endregion

