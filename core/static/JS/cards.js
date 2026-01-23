
const cards = {};
const cardsAll = document.getElementsByClassName('card');


Array.from(cardsAll).forEach(card => {
    
    const name = card.getAttribute('name');
    const isChecked = !!card.getAttribute('checked');
    
    cards[name] ??= {
        elements:[],
        current: undefined
    };
    cards[name].elements.push(card);

    if (isChecked) {
        cards[name].current = card;
    }

    card.addEventListener('click', (e)=>{

        cards[name].current?.removeAttribute('checked');
        
        cards[name].current = card;
        cards[name].current?.setAttribute('checked', true);
    });

});

window.cards = cards;
