/**
 * Gets the media stream from the browser
 * @param {MediaConstraints} constraints Media contraints defined by the MediaStream API
 * @returns MediaStream
 */
async function getMedia(constraints) {
    try {
        return await navigator.mediaDevices.getUserMedia(constraints)
    } catch (error) {
        alert(error)
        return null
    }
}

/**
 * Send a debug message to the console
 * @param {string} label Part of application that is making the call
 * @param {string} message Message body
 */
function debugLog(label, message) {
    console.log(`${('[' + label + ']').padEnd(30)} ${message}`)
}

/**
 * Creates an RTCPeerConnection with logging for debugging.
 *
 * @NOTE No connection has been established yet after this function call. The
 * connection still needs to be negotiated with the server.
 * @returns RTCPeerConnection
 */
function createPeerConnection() {
    const peerConnection = new RTCPeerConnection({
        sdpSemantics: 'unified-plan'
    })

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

/**
 * Asynchronously wait for ICE server gathering to complete
 * @param {RTCPeerConnection} peerConnection Instance of `RTCPeerConnection`
 * @returns Promise<void>
 */
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

/**
 * Establish RTC connection with server
 * @param {RTCPeerConnection} peerConnection Instance of `RTCPeerConnection`
 */
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

/**
 * Test data channel that sends ping/pong messages
 */
class PingPongDataChannel {
    interval = null
    dataChannel = null

    /**
     * Establish ping pong data channel over RTC peer connection
     * @param {RTCPeerConnection} peerConnection Instance of `RTCPeerConnection` that has already been negotiated
     */
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
            debugLog('Ping Pong Data Channel', '> ' + message)
            this.dataChannel.send(message)
        }, 1000)
    }

    onClose() {
        clearInterval(this.interval)
        debugLog('Ping Pong Data Channel', '- close')
    }

    onMessage(event) {
        debugLog('Ping Pong Data Channel', '< ' + event.data)
    }
}

/**
 * Data channel that sends metadata about the video stream
 */
class MetadataDataChannel {
    dataChannel = null
    isOpen = false

    /**
     * Establish metadata data channel over RTC peer connection
     * @param {RTCPeerConnection} peerConnection Instance of `RTCPeerConnection` that has already been negotiated
     */
    constructor(peerConnection) {
        this.dataChannel = peerConnection.createDataChannel('metadata', {
            ordered: true
        })

        this.dataChannel.onopen = this.onOpen.bind(this)
        this.dataChannel.onclose = this.onClose.bind(this)
    }

    /**
     * Asynchronously wait for connection to peer to be established
     * @returns Promise<void>
     */
    waitForOpen() {
        return new Promise((resolve) => {
            if (this.isOpen) {
                resolve()
            }

            const listener = this.dataChannel.addEventListener(
                'open',
                () => {
                    this.dataChannel.removeEventListener('close', listener)
                    resolve()
                },
                false
            )
        })
    }

    onOpen() {
        debugLog('Metadata Data Channel', '- open')
        this.isOpen = true
    }

    onClose() {
        debugLog('Metadata Data Channel', '- close')
    }

    sendMetadata(width, height, framerate) {
        const payload = JSON.stringify({ width, height, framerate })

        debugLog('Metadata Data Channel', '> ' + payload)
        this.dataChannel.send(payload)
    }
}

/**
 * Data channel that measures latency over peer connection
 */
class LatencyDataChannel {
    dataChannel = null

    /**
     * Establish latency data channel over RTC peer connection
     * @param {RTCPeerConnection} peerConnection Instance of `RTCPeerConnection` that has already been negotiated
     */
    constructor(peerConnection) {
        this.dataChannel = peerConnection.createDataChannel('latency', {
            ordered: true
        })

        this.dataChannel.onopen = this.onOpen.bind(this)
        this.dataChannel.onclose = this.onClose.bind(this)
        this.dataChannel.onmessage = this.onMessage.bind(this)
    }

    onOpen() {
        debugLog('Latency Data Channel', '- open')
        debugLog('Latency Data Channel', '> -1')

        // @NOTE It is important that the client sends an initial -1 value to
        // the server. The server expects that the first message is a -1 and
        // will start the latency polling loop after it is received.
        this.dataChannel.send('-1')
    }

    onClose() {
        debugLog('Latency Data Channel', '- close')
    }

    onMessage(event) {
        debugLog('Latency Data Channel', '> ' + event.data)
        this.dataChannel.send(event.data)
        debugLog('Latency Data Channel', '< ' + event.data)
    }
}

async function main() {
    const peerConnection = createPeerConnection()
    const latencyDataChannel = new LatencyDataChannel(peerConnection)
    const metadataDataChannel = new MetadataDataChannel(peerConnection)

    const mediaStream = await getMedia({
        audio: false,
        video: { width: 640, height: 360, frameRate: { ideal: 10, max: 15 } }
    })

    // Render video preview to html video element
    let videoPreviewElement = document.getElementById('video-preview')
    videoPreviewElement.srcObject = mediaStream

    if (mediaStream.getTracks().length < 0) {
        throw new Error('Could not access video track')
    }

    if (mediaStream.getTracks().length !== 1) {
        console.warn(
            'More than 1 video track found. Only the first track will be used.'
        )
    }

    // Bind video track to RTC connection
    const track = mediaStream.getTracks()[0]
    peerConnection.addTrack(track, mediaStream)

    // Establish connection to server
    await negotiate(peerConnection)

    // Send metadata to server after initial connection
    await metadataDataChannel.waitForOpen()
    metadataDataChannel.sendMetadata(
        track.getSettings().width,
        track.getSettings().height,
        track.getSettings().frameRate
    )

    // Hide the loading spinner
    document.getElementById('spinner').classList.remove('show')
}

main().catch((error) => alert(error))