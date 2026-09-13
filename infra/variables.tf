variable "regiao" {
  description = "Região da AWS onde a instância é criada."
  type        = string
  default     = "us-east-1"
}

variable "nome" {
  description = "Prefixo usado no nome dos recursos."
  type        = string
  default     = "medassist"
}

variable "tipo_instancia" {
  description = "Tipo da instância com GPU. g6.xlarge = L4 com 24 GB de VRAM, 4 vCPUs."
  type        = string
  default     = "g6.xlarge"
}

variable "tamanho_disco_gb" {
  description = "Tamanho do disco em GB. Precisa caber o modelo base (~14 GB), datasets e índice do RAG."
  type        = number
  default     = 100
}

variable "zona_dns" {
  description = "Zona do Route 53 onde o registro é criado."
  type        = string
  default     = "ia4.dev"
}

variable "subdominio" {
  description = "Nome que aponta para a instância, dentro da zona."
  type        = string
  default     = "medassist"
}

variable "minutos_ociosidade" {
  description = "Minutos de CPU baixa antes do desligamento automático."
  type        = number
  default     = 30
}
