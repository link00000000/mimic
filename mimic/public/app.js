async function getMedia(constraints) {
    try {
        return await navigator.mediaDevices.getUserMedia(constraints)
    } catch (error) {
        alert(error)
        return null
    }
}

async function main() {
    const mediaStream = await getMedia({ audio: false, video: true })

    let videoPreviewElement = document.getElementById('video-preview')
    videoPreviewElement.srcObject = mediaStream
}

main().catch((error) => alert(error))