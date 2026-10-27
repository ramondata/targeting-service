# targeting-service (Python)

Este é o serviço de regras de segmentação (targeting) do projeto ToggleMaster. Ele é responsável por gerenciar regras complexas (ex: "50% dos usuários", "usuários do país X") para uma feature flag específica.

**IMPORTANTE:** Este serviço também é protegido e depende que o `auth-service` esteja rodando (ex: em `http://localhost:8001`).

## 📦 Pré-requisitos (Local)

* [Python](https://www.python.org/) (versão 3.9 ou superior)
* [PostgreSQL](https://www.postgresql.org/download/)
* O `auth-service` deve estar rodando.

## 🚀 Rodando Localmente

1.  **Clone o repositório** e entre na pasta `targeting-service`.

2.  **Prepare o Banco de Dados:**
    * Crie um banco de dados no seu PostgreSQL (ex: `targeting_db`).
    * Execute o script `db/init.sql` para criar a tabela `targeting_rules`:
        ```bash
        psql -U seu_usuario -d targeting_db -f db/init.sql
        ```

3.  **Configure as Variáveis de Ambiente:**
    Crie um arquivo chamado `.env` na raiz desta pasta (`targeting-service/`) com o seguinte conteúdo:
    ```.env
    # String de conexão do seu banco de dados PostgreSQL
    DATABASE_URL="postgres://SEU_USUARIO:SUA_SENHA@localhost:5432/targeting_db"
    
    # Porta que este serviço (targeting-service) irá rodar
    PORT="8003"
    
    # URL do auth-service (que deve estar rodando na porta 8001)
    AUTH_SERVICE_URL="http://localhost:8001"
    ```

4.  **Instale as Dependências:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Inicie o Serviço:**
    ```bash
    gunicorn --bind 0.0.0.0:8003 app:app
    ```
    O servidor estará rodando em `http://localhost:8003`.

## 🧪 Testando os Endpoints

Lembre-se de obter sua `SUA_CHAVE_API` no `auth-service` (veja o README do `flag-service`).

**1. Verifique a Saúde (Health Check):**
```bash
curl http://localhost:8003/health
```
Saída esperada: `{"status":"ok"}`

**2. Crie uma nova Regra de Segmentação:** Vamos criar uma regra para a flag enable-new-dashboard (que você criou no flag-service). Esta regra fará a flag aparecer para 50% dos usuários.
```bash
curl -X POST http://localhost:8003/rules \
-H "Content-Type: application/json" \
-H "Authorization: Bearer SUA_CHAVE_API" \
-d '{
    "flag_name": "enable-new-dashboard",
    "is_enabled": true,
    "rules": {
        "type": "PERCENTAGE",
        "value": 50
    }
}'
```
Saída esperada: (Um JSON com os dados da regra criada).

**3. Busque a Regra que você criou:**
```bash
curl http://localhost:8003/rules/enable-new-dashboard \
-H "Authorization: Bearer SUA_CHAVE_API"
```
Saída esperada: (O JSON da regra que você acabou de criar).

**4. Atualize a Regra (mude para 75%):**
```bash
curl -X PUT http://localhost:8003/rules/enable-new-dashboard \
-H "Content-Type: application/json" \
-H "Authorization: Bearer SUA_CHAVE_API" \
-d '{
    "rules": {
        "type": "PERCENTAGE",
        "value": 75
    }
}'
```
Saída esperada: (O JSON da regra atualizada, com `"value": 75`).

## CI/CD no AWS Academy

O pipeline da branch produtiva `aws-cloud-k8s` autentica com o repository secret
`AWS_ACADEMY_CREDENTIALS`. Cole o bloco de **AWS Details → AWS CLI**, com
`aws_access_key_id`, `aws_secret_access_key` e `aws_session_token`.
O cabeçalho `[default]` é opcional. O secret é configurado neste repositório;
o secret do auth-service não é compartilhado automaticamente.

O workflow usa `ramondata/CI-reusable-source`, fixado por SHA, no modo Academy.
As credenciais são validadas e mascaradas, sem assumir uma role via OIDC.
O código-fonte e a imagem passam pelas verificações antes da publicação no ECR.
Pull requests executam somente as verificações, sem autenticar na AWS.

| Variável opcional | Valor padrão |
| --- | --- |
| `AWS_REGION` | `us-east-1` |
| `ECR_REPOSITORY` | `toggle-master/targeting-service` |
| `APP_VERSION` | `v1.0.0` |

O ECR deve existir na conta e região do laboratório. A tag publicada segue
`APP_VERSION-SHA_CURTO`, por exemplo `v1.0.0-abcdef1`.

A cada reinício do laboratório, substitua o bloco inteiro do secret e use
**Re-run all jobs** numa execução por push que já contenha esta alteração.
Alterar o secret não dispara o pipeline. O botão **Run workflow** depende de
este arquivo também existir na branch padrão do repositório.

### GitOps automático

Após a publicação da imagem, o pipeline atualiza automaticamente o repositório
existente `ramondata/toggle-master-gitops`. Configure `GITOPS_DEPLOY_KEY` neste
repositório com uma chave privada autorizada a escrever no GitOps.
Os pushes fazem rebase e até três tentativas para acomodar atualizações de
outros serviços na mesma branch sem usar force push.
O job atualiza repositório e tag em `apps/targeting-service/values.yaml`, na
`master`. A configuração de ArgoCD e do cluster é uma etapa separada.
