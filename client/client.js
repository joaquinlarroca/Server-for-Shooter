const socket = new WebSocket("ws://127.0.0.1:443");
let publicKeyPem = undefined

function str2ab(str) {
    const buf = new ArrayBuffer(str.length);
    const bufView = new Uint8Array(buf);
    for (let i = 0, strLen = str.length; i < strLen; i++) {
        bufView[i] = str.charCodeAt(i);
    }
    return buf;
}

async function importRsaKey(pem) {
    // fetch the part of the PEM string between header and footer
    const pemHeader = "-----BEGIN PUBLIC KEY-----";
    const pemFooter = "-----END PUBLIC KEY-----";
    const pemContents = pem.substring(
        pemHeader.length,
        pem.length - pemFooter.length - 1,
    );
    // base64 decode the string to get the binary data
    const binaryDerString = window.atob(pemContents);
    // convert from a binary string to an ArrayBuffer
    const binaryDer = str2ab(binaryDerString);

    return await window.crypto.subtle.importKey(
        "spki",
        binaryDer,
        {
            name: "RSA-OAEP",
            hash: "SHA-256",
        },
        true,
        ["encrypt"],
    );
}

async function encryptData(data) {
    try {
        const publicKey = await importRsaKey(publicKeyPem);

        const encodedData = new TextEncoder().encode(data);
        const encryptedData = await crypto.subtle.encrypt(
            {
                name: "RSA-OAEP",
                hash: "SHA-256",
            },
            publicKey,
            encodedData
        );
        let base64EncodedData = btoa(String.fromCharCode(...new Uint8Array(encryptedData)));

        return base64EncodedData

    } catch (error) {
        console.error("Error importing key or encrypting data:", error);
        return null;
    }
}

socket.onopen = () => {
    console.log("Connected");
};

socket.onmessage = async (event) => {
    console.log(event.data);
    document.body.innerHTML += event.data + "<br> <br>";

    const data = JSON.parse(event.data);
    if (data.type === 'server') {
        publicKeyPem = data['public-key'];

        socket.send(JSON.stringify({ type: "register", username: "test", password: await encryptData("test") }));

    }
    if (data.type === 'sign_response' && data.data == "User already exists") {
        try {
            socket.send(JSON.stringify({ type: "login", username: "test", password: await encryptData("test") }));
    
        } catch (error) {
            console.log(error);

        }
    }
};
socket.onclose = (event) => {
    console.log("Connection closed", event);
}
socket.onerror = (error) => {
    console.log("Error", error);
}