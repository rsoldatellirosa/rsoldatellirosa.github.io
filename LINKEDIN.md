# Rascunhos automáticos para LinkedIn

Depois de uma publicação bem-sucedida do GitHub Pages em `main`, a automação
`Rascunhos LinkedIn` confere o catálogo `src/portfolio-cases.json` e gera um arquivo
`.txt` para cada caso que ainda não tem rascunho registrado.

**Nenhum post é enviado ao LinkedIn.** A automação não usa credenciais nem API do
LinkedIn. Revise e publique o texto manualmente no seu perfil.

## Onde pegar os textos

1. Abra https://github.com/rsoldatellirosa/rsoldatellirosa.github.io/actions/workflows/linkedin-drafts.yml.
2. Abra a execução concluída mais recente que informa ter preparado rascunhos.
3. O texto completo aparece no **resumo da execução**, em um bloco para copiar.
4. Revise, copie o texto e cole no LinkedIn. Não é necessário baixar arquivos.

O download em **Artifacts > rascunhos-linkedin** continua disponível como opção.
Execuções sem casos novos exibem links para os rascunhos anteriores.

Os arquivos ficam guardados como artefatos por 90 dias, conforme os limites do
repositório. Eles não entram no site. Como o repositório é público, não considere
artefatos ou logs um lugar privado; somente conteúdo público aprovado pode entrar
nesse fluxo. Não registre dados de clientes nem credenciais.

## Adicionar o próximo caso

1. Crie dois arquivos HTML em `src/`: o relato do caso (PT/EN, classe `prob`) e o
   cartão do projeto (PT/EN, classe `repo-card`). Use os arquivos
   `portfolio-bandwidth-case.html` e `portfolio-bandwidth-project.html` como modelo.
2. Adicione uma entrada em `src/portfolio-cases.json`, com ID permanente, título,
   os dois caminhos e o repositório público de `rsoldatellirosa`.
3. O `id` do bloco do relato precisa corresponder ao ID do catálogo.
4. Rode `npm run build`, `npm test` e `npm run test:linkedin`.
5. Publique em `main`. O gerador inclui os casos na experiência da Hapolo e na
   lista de projetos. A automação aguarda o Pages publicar para preparar o post.

O catálogo atual se destina aos casos da Hapolo. Para casos de outras experiências,
ajuste a localização no gerador conscientemente antes de cadastrar. Não reescreva
os arquivos em `src/original/` para adicionar conteúdo.

Edições de layout, favicon ou texto de um caso já registrado não geram outro
rascunho. O ID é a identidade do caso; não troque o ID para corrigir sua redação.

## Gerar novamente

Em **Actions > Rascunhos LinkedIn > Run workflow**, mantenha a branch `main`,
informe o `case_id` e marque **Gerar novamente**. Deixe o ID vazio para selecionar
todos os casos ainda não processados. Se marcar gerar novamente com ID vazio,
todos os casos serão refeitos. A opção **Usar IA** fica ligada por padrão; pode
ser desligada em uma execução manual para usar somente o texto aprovado, sem chamar a API.

## Modo sem chave de IA (já funciona)

Sem `OPENAI_API_KEY`, o programa usa o texto aprovado em português do caso,
organiza as frases em parágrafos e acrescenta links fixos para o caso e o GitHub.
Esse modo não faz chamadas à OpenAI e não precisa de conta de API.

## Ativar reescrita com IA (opcional)

1. Em **Settings > Secrets and variables > Actions > New repository secret**,
   crie `OPENAI_API_KEY` com sua chave da API OpenAI. Não cole a chave no código,
   no chat, em comentários ou em arquivos versionados.
2. Opcionalmente crie a variável `PORTFOLIO_POST_MODEL`. O padrão é `gpt-5-mini`.
3. Gere novamente um caso pelo botão **Run workflow** para conferir o resultado.

A API requer conta, acesso ao modelo e faturamento disponíveis; a assinatura do
aplicativo, sozinha, não configura essa integração. O processamento pela API pode
gerar custo. Cada caso faz no máximo uma chamada de geração, com limite de saída.

O modelo recebe o relato público aprovado e o README público do repositório como
contexto. As regras estão em `.github/prompts/linkedin.md`: PT-BR, primeira pessoa,
sem travessões, sem inventar números ou extrapolar resultados. O modelo não tem
ferramentas para executar código ou publicar. Falhas de API ou texto inválido
fazem o programa usar o texto aprovado. A revisão humana continua necessária:
validação automática de números não prova todas as afirmações de um texto.

## Controle de duplicação e falhas

A branch `codex/linkedin-state` guarda `generated-cases.json`, com IDs dos casos,
hash do texto, modo de geração e URL da execução que guarda o rascunho. Ela é
separada de `main`, não altera a origem do Pages e não é a branch de backup.

O registro só é atualizado depois de o upload do artefato terminar. As execuções
são serializadas. Não apague essa branch para limpar rascunhos, pois isso remove
o histórico e os casos poderão ser gerados novamente. Se o upload funcionar mas
o registro falhar, a execução termina em erro e uma nova tentativa poderá gerar
outro arquivo; confira o artefato da execução anterior antes de repetir.

## Testar localmente

```powershell
npm run test:linkedin
python tools/generate_linkedin_drafts.py --case-id caso-banda-digitalocean
```

Os testes não acessam APIs nem enviam mensagens. Os arquivos locais ficam em
`linkedin-drafts/`, ignorados pelo Git e excluídos do site. No uso local, sem
`--github-state`, o programa não consulta nem atualiza o registro remoto.
