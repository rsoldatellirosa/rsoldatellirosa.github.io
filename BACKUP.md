# Recuperar o portfólio anterior

O backup foi concluído e verificado antes de alterar a pasta do projeto.

## Cópias no computador

Na pasta `Desktop/work/portfolio/backups/portfolio-antes-landing-2026-10-20`:

- `desktop-completo-incluindo-git.zip`: todos os arquivos do projeto local anterior, incluindo `.git`. Commit local: `6914b1a013d504afbb759f069c32176bb73219c5`.
- `site-atual-no-github.zip`: versão que estava publicada. Commit: `bddbbb15c6c7233fc9a6e3f976547754bec773c9`.
- `historico-completo.bundle`: histórico Git e referências da versão publicada.
- `manifesto.json`: hashes SHA-256 dos arquivos e dos backups.

Para consultar ou recuperar uma cópia local, extraia o ZIP desejado em uma pasta nova. Isso preserva o projeto novo. Para recuperar o histórico em uma pasta nova:

```powershell
git clone historico-completo.bundle portfolio-recuperado
```

## Cópias no GitHub

- [Branch com a versão antiga](https://github.com/rsoldatellirosa/rsoldatellirosa.github.io/tree/codex/backup-portfolio-antes-landing-2026-10-20)
- [Tag de backup](https://github.com/rsoldatellirosa/rsoldatellirosa.github.io/tree/backup-portfolio-antes-landing-2026-10-20)
- [Baixar os arquivos antigos em ZIP](https://github.com/rsoldatellirosa/rsoldatellirosa.github.io/archive/refs/tags/backup-portfolio-antes-landing-2026-10-20.zip)

## Colocar a versão antiga no ar

1. Abra [Settings > Pages do repositório](https://github.com/rsoldatellirosa/rsoldatellirosa.github.io/settings/pages).
2. Na seção de publicação por branch, selecione `codex/backup-portfolio-antes-landing-2026-10-20`, mantendo `/(root)`.
3. Salve e aguarde o GitHub Pages concluir a publicação.

Esse caminho publica diretamente a cópia antiga, preservando a nova versão e seu histórico. Para voltar à nova versão depois, selecione `main` novamente, desde que o PR da nova versão já tenha sido mesclado. Enquanto a origem estiver na branch de backup, envios para `main` não mudarão o site publicado.

O repositório continua configurado para publicar `main`; a origem de publicação não foi alterada durante esta preparação.
