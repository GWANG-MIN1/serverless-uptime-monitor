# 03. CI 품질 게이트 (ruff / terraform fmt / tfsec)

## 목표
현재 CI(`.github/workflows/deploy.yml`)는 `pytest` 만 돈다.
배포 전에 **코드 스타일·포맷·IaC 보안**을 자동 검사하는 게이트를 추가한다.

## 추가할 검사
| 도구 | 대상 | 역할 |
|---|---|---|
| `ruff` | Python | 린트 + 포맷 검사 |
| `terraform fmt -check` | Terraform | 포맷 일관성 |
| `terraform validate` | Terraform | 문법/참조 검증 (이미 deploy job 에 있음) |
| `tfsec` 또는 `checkov` | Terraform | IaC 보안 취약점 정적분석 |

## 구현 개요 (내일 진행)
`test` job 에 단계 추가 (deploy 전에 실패하면 배포 중단):

```yaml
- name: Ruff
  run: |
    pip install ruff
    ruff check .

- name: Terraform fmt check
  run: terraform -chdir=terraform fmt -check -recursive

- name: tfsec
  uses: aquasecurity/tfsec-action@v1.0.0
  with: { working_directory: terraform }
```

- [ ] `pyproject.toml` 의 `[tool.ruff]` 규칙 확정 (스켈레톤은 이미 추가됨)
- [ ] `ruff check .` 통과하도록 기존 코드 정리
- [ ] `terraform fmt` 한 번 돌려 포맷 정렬
- [ ] tfsec 경고 검토 후 필요한 것만 `#tfsec:ignore` 처리

## 면접 포인트
"배포 파이프라인에 린트와 IaC 보안 스캔을 게이트로 넣어 품질을 자동으로 강제했습니다."
