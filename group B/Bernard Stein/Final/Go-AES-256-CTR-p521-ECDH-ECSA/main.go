package main

import (
	"fmt"
	"net/http"
	"sync"
	"github.com/gorilla/websocket"
)


type Message struct {
	Type              string `json:"type"`
	Username          string `json:"username,omitempty"`
	Ciphertext  	  string `json:"ciphertext,omitempty"`
	SenderPublicKey   string `json:"senderPublicKey,omitempty"`
	ReceiverPublicKey string `json:"receiverPublicKey,omitempty"`
	Signature         string `json:"signature,omitempty"`
	IV                string `json:"iv,omitempty"`
}

var (
	clients   = make(map[*websocket.Conn]string) // map to store clients
	broadcast = make(chan Message)
	upgrader  = websocket.Upgrader{
		CheckOrigin: func(r *http.Request) bool {
			return true
		},
	}
	mu sync.Mutex // mutex to synchronize access to shared resources
)

func main() {
	http.HandleFunc("/", handleHome)
	http.HandleFunc("/ws", handleConnections)

	// Goroutine to handle messages and broadcast them to clients
	go handleMessages()

	fmt.Println("Server started on :8080")
	http.ListenAndServe(":8080", nil)
}

func handleHome(w http.ResponseWriter, r *http.Request) {
	http.ServeFile(w, r, "index.html")
}

func handleConnections(w http.ResponseWriter, r *http.Request) {
	// Upgrade initial GET request to a websocket
	ws, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		fmt.Printf("Error upgrading to websocket: %v\n", err)
		return
	}

	// Register new client
	addClient(ws)

	// Ensure client removal when function exits
	defer func() {
		removeClient(ws)
		ws.Close()
	}()

	// Listen for incoming messages from this client
	for {
		var msg Message
		err := ws.ReadJSON(&msg)
		fmt.Print("Message Recieved:", msg)
		if err != nil {
			fmt.Printf("Error reading JSON message: %v\n", err)
			removeClient(ws)
			break
		}

		// If message is a public key exchange, save the public key
		if msg.Type == "exchangePublicKeys" {
			updateClientPublicKey(ws, msg.SenderPublicKey)

			// Broadcast the new client's public key to all other clients
			broadcast <- msg

			// Send all previously connected clients' public keys to the newly connected client
			mu.Lock()
			for client, publicKey := range clients {
				if client != ws && publicKey != "" {
					// Send existing client's public key to the newly connected client
					existingKeyMsg := Message{
						Type:            "exchangePublicKeys",
						SenderPublicKey: publicKey,
					}
					if err := ws.WriteJSON(existingKeyMsg); err != nil {
						fmt.Printf("Error sending existing public key to new client: %v\n", err)
					}
				}
			}
			mu.Unlock()

			continue
		}

		// Send the message to the broadcast channel
		broadcast <- msg
	}
}

func handleMessages() {
	for {
		msg := <-broadcast
		fmt.Printf("Broadcasting message: %+v\n", msg)

		mu.Lock()
		for client, publicKey := range clients {
			// Handle broadcasting public keys to all clients except the sender
			if msg.Type == "exchangePublicKeys" && msg.SenderPublicKey != publicKey {
				if err := client.WriteJSON(msg); err != nil {
					fmt.Printf("Error broadcasting public key: %v\n", err)
					client.Close()
					delete(clients, client)
				}
			}

			// Handle encrypted message broadcasting
			if msg.Type == "encryptedMessage" && msg.ReceiverPublicKey == publicKey {
				if err := client.WriteJSON(msg); err != nil {
					fmt.Printf("Error broadcasting encrypted message: %v\n", err)
					client.Close()
					delete(clients, client)
				}
			}
		}
		mu.Unlock()
	}
}

func addClient(ws *websocket.Conn) {
	mu.Lock()
	defer mu.Unlock()
	clients[ws] = ""
}

func removeClient(ws *websocket.Conn) {
	mu.Lock()
	defer mu.Unlock()
	delete(clients, ws)
}

func updateClientPublicKey(ws *websocket.Conn, publicKey string) {
	mu.Lock()
	defer mu.Unlock()
	clients[ws] = publicKey
}

