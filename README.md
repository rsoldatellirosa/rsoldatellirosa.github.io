# Portfólio de Rodrigo Soldatelli da Rosa

Site estático, bilíngue em português e inglês, com landing page, portfólio completo e stack. Os arquivos prontos ficam na raiz e podem ser servidos diretamente, sem Node.js ou processo de build no servidor.

## Arquivos

- `index.html`: landing aprovada, com apresentação, stack, Mutirão, Aulia e contato.
- `portfolio.html`: conteúdo detalhado do portfólio original, preservado em PT/EN.
- `stack.html`: stack completa.
- `assets/`: retrato de alta resolução, marca da Hapolo e licença dos ícones Lucide.
- `src/`: fontes editáveis, imagens e cópias originais usadas para conferir os textos.
- `tools/`: geração das páginas, geração dos ícones e verificações de navegação.
- `BACKUP.md`: localização dos backups e instruções para restaurar a versão anterior.

## Testar no computador

Com Python instalado, abra um terminal nesta pasta e execute:

```powershell
python -m http.server 8765 --bind 127.0.0.1
```

Abra http://127.0.0.1:8765/. Use Ctrl + F5 depois de alterar os arquivos.

## Editar e gerar novamente

Edite `src/portfolio-cinematico-template.html`, `src/portfolio-cinematico.css`, `src/portfolio-navegacao.css` ou `src/portfolio-duas-paginas.js`. Depois execute:

```powershell
python tools/build-portfolio-duplo.py
```

O gerador usa apenas a biblioteca padrão do Python. Ele verifica se os textos completos em PT/EN continuam iguais aos originais, se os links internos encontram seus destinos e se as imagens foram copiadas sem alteração.

## Verificações de navegação

Com Node.js instalado:

```powershell
npm ci
npm test
```

As dependências são usadas somente no desenvolvimento. A verificação executa os controles de idioma e tema sobre o HTML gerado e confere navegação, preferências salvas, links, retorno ao topo e ícones. Ela não substitui a revisão visual no navegador ou uma auditoria manual de acessibilidade. Para regenerar os SVGs do catálogo, execute `npm run icons` antes de gerar as páginas.

## Publicação

O GitHub Pages publica a raiz da branch `main`. A nova versão foi preparada em `codex/portfolio-landing-2026-10-20`, separada do site no ar. Publicar exige aprovar e mesclar o PR dessa branch, ou enviar os arquivos aprovados para `main`.

As pastas de desenvolvimento estão excluídas da saída do GitHub Pages em `_config.yml`. Antes de publicar, confira a revisão visual e rode `/a11y-audit` se disponível.

O conteúdo técnico não deve incluir nomes de clientes, endereços de servidores ou credenciais. Preserve os textos originais da página completa; as alterações de apresentação ficam na landing.

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
