# rsoldatellirosa.github.io

Portfólio pessoal — Rodrigo Soldatelli da Rosa.

Site estático de arquivo único (`index.html`), bilíngue PT/EN, sem build e sem
dependência externa. CSS e JS inline; o seletor de idioma alterna blocos
`.lang-pt` / `.lang-en` e guarda a preferência em `localStorage`.

## Domínio próprio

Para apontar um domínio comprado para cá:

1. Criar um arquivo `CNAME` na raiz deste repositório com o domínio, sem
   protocolo e sem barra final. Exemplo: `rodrigosoldatelli.dev`
2. No painel do registrador, criar os registros DNS:
   - 4 registros `A` para o apex, apontando para
     `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - 1 registro `CNAME` para `www`, apontando para `rsoldatellirosa.github.io`
3. Em Settings > Pages, preencher o campo *Custom domain* e aguardar a
   verificação; depois marcar *Enforce HTTPS* (o certificado leva alguns minutos).

## Conteúdo

O trabalho de infraestrutura descrito nos estudos de caso é intencionalmente
publicado sem nome de cliente, endereço de servidor, credencial ou nome de
serviço interno.
