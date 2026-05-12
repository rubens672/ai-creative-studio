#!/bin/bash
REGION="us-central1"

AGENTS=("brand-strategist-agent" "copywriter-agent" "critic-agent" "designer-agent" "project-manager-agent")

for AGENT in "${AGENTS[@]}"; do
  echo "Aggiornando $AGENT..."
  
  # Trova l'URL
  URL=$(gcloud run services describe $AGENT --region $REGION --format="value(status.url)")
  
  if [ -z "$URL" ]; then
    echo "Errore: impossibile trovare l'URL per $AGENT"
    continue
  fi
  
  # Estrai solo il dominio (rimuovi https://)
  PUBLIC_HOST=$(echo $URL | sed 's|https://||')
  
  echo "Trovato host: $PUBLIC_HOST"
  
  # Aggiorna le variabili d'ambiente
  gcloud run services update $AGENT \
    --region $REGION \
    --update-env-vars="PUBLIC_HOST=$PUBLIC_HOST,PUBLIC_PORT=443,PROTOCOL=https" \
    --quiet
    
  echo "$AGENT aggiornato con successo!"
  echo "------------------------"
done
