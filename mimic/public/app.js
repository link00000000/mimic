// Milliseconds to wait before resfreshing the page on error
const RESFRESH_TIMEOUT = 1000

// Default video constraints
CONSTRAINTS = {
    audio: false,
    video: {
        width: 640,
        height: 480,
        frameRate: 30
    }
}

/**
 * Enable `console.log` in iOS safari.
 *
 * By default, `console.log` is NOP in iOS Safari.
 */
function enableSafariConsoleLog() {
    var userAgent = window.navigator.userAgent

    if (userAgent.match(/iPad/i) || userAgent.match(/iPhone/i)) {
        console.log = console.info
    }
}

/**
 * Gets the media stream from the browser
 * @param {MediaConstraints} constraints Media contraints defined by the MediaStream API
 * @returns MediaStream
 */
async function getMedia(constraints) {
    return await navigator.mediaDevices.getUserMedia(constraints)
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
    const response = await fetch('/offer', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            sdp: localDescription.sdp,
            type: localDescription.type
        })
    })

    switch (response.status) {
        case 409:
            throw new Error(
                'Mimic camera already in use. Only 1 device can be connected to Mimic at a time.'
            )

        case 500:
            throw new Error(
                'Something went wrong, try again later or restart Mimic.'
            )
    }

    const answer = await response.json()
    await peerConnection.setRemoteDescription(answer)
}

/**
 * Test data channel that sends ping/pong messages
 */
class PingPongDataChannel {
    /**
     * Establish ping pong data channel over RTC peer connection
     * @param {RTCPeerConnection} peerConnection Instance of `RTCPeerConnection` that has already been negotiated
     */
    constructor(peerConnection) {
        this.interval = null
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
    /**
     * Establish metadata data channel over RTC peer connection
     * @param {RTCPeerConnection} peerConnection Instance of `RTCPeerConnection` that has already been negotiated
     */
    constructor(peerConnection) {
        this.isOpen = false
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
        const payload = JSON.stringify({
            width,
            height,
            framerate
        })

        debugLog('Metadata Data Channel', '> ' + payload)
        this.dataChannel.send(payload)
    }
}

/**
 * Data channel that measures latency over peer connection
 */
class LatencyDataChannel {
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

/**
 * Reuse existing RTP Sender to send a different video stream without the need
 * of renegotiation.
 * @param {RTCRtpSender} sender Sender that is sending the video stream
 * @param {RTCDataChannel} metadataDataChannel Data channel used to send video
 * track metadata
 */
async function replaceVideoTrack(sender, metadataDataChannel) {
    const mediaDevices = await getMedia(CONSTRAINTS)

    if (mediaDevices.getVideoTracks().length < 0) {
        throw new Error('Could not access video track')
    }

    if (mediaDevices.getVideoTracks().length !== 1) {
        console.warn(
            'More than 1 video track found. Only the first track will be used.'
        )
    }

    const track = mediaDevices.getVideoTracks()[0]

    // Send metadata to server
    await metadataDataChannel.waitForOpen()
    metadataDataChannel.sendMetadata(
        track.getSettings().width,
        track.getSettings().height,
        track.getSettings().frameRate
    )

    // Replace current video track with new track
    sender.replaceTrack(track)

    return mediaDevices
}

async function main() {
    enableSafariConsoleLog()

    const peerConnection = createPeerConnection()
    const latencyDataChannel = new LatencyDataChannel(peerConnection)
    const metadataDataChannel = new MetadataDataChannel(peerConnection)

    const mediaDevices = await getMedia(CONSTRAINTS)

    // Render video preview to html video element
    let videoPreviewElement = document.getElementById('video-preview')
    videoPreviewElement.srcObject = mediaDevices

    if (mediaDevices.getVideoTracks().length < 0) {
        throw new Error(
            'Could not access video track, try refreshing the page.'
        )
    }

    if (mediaDevices.getVideoTracks().length !== 1) {
        console.warn(
            'More than 1 video track found. Only the first track will be used.'
        )
    }

    // Bind video track to RTC connection
    const track = mediaDevices.getTracks()[0]
    const sender = peerConnection.addTrack(track, mediaDevices)

    // Establish connection to server
    await negotiate(peerConnection)

    // Send metadata to server after initial connection
    await metadataDataChannel.waitForOpen()
    metadataDataChannel.sendMetadata(
        track.getSettings().width,
        track.getSettings().height,
        track.getSettings().frameRate
    )

    // Close connection when page closes
    window.addEventListener(
        'beforeunload',
        () => {
            peerConnection.close()
        },
        false
    )

    // Update the video track to use new resolution on orientation change
    window.addEventListener(
        'orientationchange',
        async() => {
            const mediaDevices = await replaceVideoTrack(
                sender,
                metadataDataChannel
            )
            videoPreviewElement.srcObject = mediaDevices
        },
        false
    )
  
    document.getElementById('spinner').classList.remove('show')

}

main().catch((error) => {
    const errorMessage = error instanceof Error ? error.message : error
    alert(errorMessage + '\n\n*This page will automatically refresh.*')

    // Wait for some time before refreshing incase the user cannot close the
    // window with the alert open. We don't want their browser to get stuck in a
    // refresh loop.
    setTimeout(() => window.location.reload(), REFRESH_TIMEOUT)
})
