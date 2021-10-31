package main

import (
	"flag"
	"log"
	"net/http"
)

func serveHome(w http.ResponseWriter, r *http.Request) {
	http.ServeFile(w, r, "home.html")
}

func main() {
	flag.Parse()
	var addr = flag.String("addr", ":8080", "http service address")
	http.HandleFunc("/", serveHome)
	err := http.ListenAndServe(*addr, nil)
	if err != nil {
		log.Fatal("ListenAndServe ERROR:", err)
	}
}
