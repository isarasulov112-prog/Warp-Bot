FROM golang:1.20-alpine AS builder
WORKDIR /app
COPY . .
RUN go build -mod=mod -o main main.go

FROM alpine:latest
WORKDIR /app
COPY --from=builder /app/main .
CMD ["./main"]
