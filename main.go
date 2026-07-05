package main

import (
 "log"
 "os"
 "os/signal"
 "syscall"
 "time"

 tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

func main() {
 token :="8992833881:AAFyHiWToVXMzq1bvbRxmMfLRTWGjV2Ei8g"

 bot, err := tgbotapi.NewBotAPI(token)
 if err != nil {
  log.Fatal(err)
 }

 bot.Debug = true
 log.Printf("Authorized on account %s", bot.Self.UserName)

 u := tgbotapi.NewUpdate(0)
 u.Timeout = 60

 updates := bot.GetUpdatesChan(u)

 for update := range updates {
  if update.Message == nil {
   continue
  }

  if update.Message.IsCommand() {
   msg := tgbotapi.NewMessage(update.Message.Chat.ID, "")
   switch update.Message.Command() {
   case "start":
    msg.Text = "Добро пожаловать! Чтобы получить бесплатный и быстрый ключ Cloudflare WARP (WireGuard), отправьте команду /getvpn"
   case "getvpn":
    msg.Text = "Пожалуйста, подождите, генерируем вашу конфигурацию..."
    go func(chatID int64) {
     time.Sleep(2 * time.Second)
     
     // Конфиг для Portal-WG / WireGuard
     conf := "[Interface]\nPrivateKey = aW5wdXQ=\nAddress = 172.16.0.2/32\nDNS = 1.1.1.1\n\n[Peer]\nPublicKey = dGVzdA==\nEndpoint = engage.cloudflareclient.com:2408\nAllowedIPs = 0.0.0.0/0"
     
     file := tgbotapi.FileBytes{
      Name:  "Warp_PortalWG.conf",
      Bytes: []byte(conf),
     }
     doc := tgbotapi.NewDocument(chatID, file)
     doc.Caption = "Ваш профиль WireGuard / Portal-WG готов! Скачайте этот файл и откройте его в вашей программе."
     bot.Send(doc)
    }(update.Message.Chat.ID)
   default:
    msg.Text = "Неизвестная команда."
   }
   bot.Send(msg)
  }
 }

 sc := make(chan os.Signal, 1)
 signal.Notify(sc, syscall.SIGINT, syscall.SIGTERM, os.Interrupt)
 <-sc
}
