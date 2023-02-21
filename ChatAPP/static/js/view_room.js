const scrollToBottom = (id) => {
    const element = document.getElementById(id);
    element.scrollTop = element.scrollHeight;
}

const realoader= async () => {
    let room_id = document.getElementById('room_id')

        let response = await fetch('http://192.168.1.40/messages/total/' + room_id.textContent + '/', {
            method: 'GET',
        } )

        if(response.ok) {
            return response.json()
        }
    }


const reloadIfChangeMessages = () => {
    let previousCount = undefined
    let actualCount = undefined

    return setInterval(() => {

        realoader().then(r => {
            console.log('Numero messaggi nella chat corrente ---> ' + r[0])
            console.log('previousCount ----> ' + previousCount ? previousCount : 'nessuna modifica rilevata')
            console.log('previousCount ----> ' + actualCount ? actualCount : 'nessuna modifca rilevata')

            if (previousCount === undefined) {
                previousCount = r[0]
            } else {
                actualCount = r[0]
            }

            if (previousCount && actualCount) {
                if (previousCount !== actualCount) {
                    console.log('ricarico pagina')
                    location.reload()
                }
            }

        })
    }, 5000)
}



let to_scroll = document.getElementById('to_scroll')
to_scroll.scrollTop = to_scroll.scrollHeight * 2

reloadIfChangeMessages()


