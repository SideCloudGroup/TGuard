#!/bin/bash

# TGuard Setup Script
# This script helps you set up TGuard quickly

set -e

echo "🤖 TGuard Setup Script"
echo "======================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p static/images

# Copy config file if it doesn't exist
if [ ! -f config.toml ]; then
    echo "📝 Creating config.toml from template..."
    cp config.toml.example config.toml
    echo "⚠️  Please edit config.toml with your actual values before starting the bot!"
else
    echo "✅ config.toml already exists"
fi

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your actual values if needed!"
else
    echo "✅ .env already exists"
fi

# Build Docker images
echo "🐳 Building Docker images..."
docker-compose build

# Start PostgreSQL
echo "🗄️  Starting PostgreSQL..."
docker-compose up -d postgres

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 10

# Check if PostgreSQL is ready
until docker-compose exec postgres pg_isready -U postgres; do
    echo "⏳ Waiting for PostgreSQL..."
    sleep 2
done

echo "✅ PostgreSQL is ready!"

# Prompt user to configure the bot
echo ""
echo "🔧 Configuration Steps:"
echo "1. Edit config.toml with your Bot Token and hCaptcha keys"
echo "2. Update the base_url in config.toml with your domain"
echo "3. Run 'docker-compose up -d' to start all services"
echo ""

# Offer to open config file
read -p "🤔 Do you want to edit config.toml now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v nano &> /dev/null; then
        nano config.toml
    elif command -v vim &> /dev/null; then
        vim config.toml
    elif command -v code &> /dev/null; then
        code config.toml
    else
        echo "📝 Please edit config.toml with your favorite text editor"
    fi
fi

# Final instructions
echo ""
echo "🚀 Setup Complete!"
echo ""
echo "Next steps:"
echo "1. Make sure you've configured config.toml with your actual values"
echo "2. Run: docker-compose up -d"
echo "3. Check status: docker-compose ps"
echo "4. View logs: docker-compose logs -f"
echo ""
echo "📚 For more information, check README.md"
echo "🐛 Issues? Visit: https://github.com/yourrepo/tguard/issues"
