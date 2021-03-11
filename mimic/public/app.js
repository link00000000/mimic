async function getMedia(constraints) {
    try {
        return await navigator.mediaDevices.getUserMedia(constraints)
    } catch (error) {
        alert(error)
        return null
    }
}

function debugLog(label, message) {
    console.log(`${('[' + label + ']').padEnd(30)} ${message}`)
}

function createPeerConnection() {
    const peerConnection = new RTCPeerConnection({
        sdpSemantics: 'unified-plan'
    })

    // register some listeners to help debugging
    peerConnection.addEventListener(
        'icegatheringstatechange',
        function() {
            debugLog(
                'Ice Gathering State Change',
                peerConnection.iceGatheringState
            )
        },
        false
    )
    debugLog('Ice Gathering State Change', peerConnection.iceGatheringState)

    peerConnection.addEventListener(
        'iceconnectionstatechange',
        function() {
            debugLog(
                'Ice Connection State Change',
                peerConnection.iceConnectionState
            )
        },
        false
    )
    debugLog('Ice Connection State Change', peerConnection.iceConnectionState)

    peerConnection.addEventListener(
        'signalingstatechange',
        function() {
            debugLog('Signal State Change', peerConnection.signalingState)
        },
        false
    )
    debugLog('Signal State Change', peerConnection.signalingState)

    return peerConnection
}

function waitForIce(peerConnection) {
    return new Promise(function(resolve) {
        if (peerConnection.iceGatheringState === 'complete') {
            resolve()
        } else {
            function checkState() {
                if (peerConnection.iceGatheringState === 'complete') {
                    peerConnection.removeEventListener(
                        'icegatheringstatechange',
                        checkState
                    )
                    resolve()
                }
            }
            peerConnection.addEventListener(
                'icegatheringstatechange',
                checkState
            )
        }
    })
}

async function negotiate(peerConnection) {
    const offer = await peerConnection.createOffer()
    await peerConnection.setLocalDescription(offer)

    await waitForIce(peerConnection)

    const localDescription = peerConnection.localDescription
    const response = await fetch('/webrtc-offer', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            sdp: localDescription.sdp,
            type: localDescription.type
        })
    })

    const answer = await response.json()
    await peerConnection.setRemoteDescription(answer)
}

class PingPongDataChannel {
    interval = null
    dataChannel = null

    constructor(peerConnection) {
        this.dataChannel = peerConnection.createDataChannel('chat', {
            ordered: true
        })

        this.dataChannel.onopen = this.onOpen.bind(this)
        this.dataChannel.onclose = this.onClose.bind(this)
        this.dataChannel.onmessage = this.onMessage.bind(this)
    }

    onOpen() {
        debugLog('Ping Pong Data Channel', '- open')
        this.interval = setInterval(() => {
            const message = 'ping ' + new Date().getTime()
            debugLog('Data Channel', '> ' + message)
            this.dataChannel.send(message)
        }, 1000)
    }

    onClose() {
        clearInterval(this.interval)
        debugLog('Ping Pong Data Channel', '- close')
    }

    onMessage(event) {
        debugLog('Data Channel', '< ' + event.data)
    }
}

async function main() {
    const peerConnection = createPeerConnection()
    const pingPong = new PingPongDataChannel(peerConnection)

    const mediaStream = await getMedia({
        audio: false,
        video: { width: 1280, height: 720 }
    })

    let videoPreviewElement = document.getElementById('video-preview')
    videoPreviewElement.srcObject = mediaStream

    mediaStream.getTracks().forEach((track) => {
        peerConnection.addTrack(track, mediaStream)
    })

    await negotiate(peerConnection)
}

main().catch((error) => alert(error))