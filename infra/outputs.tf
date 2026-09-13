output "instancia_id" {
  description = "Identificador da instância, usado pelo script de ligar e desligar."
  value       = aws_instance.assistente.id
}

output "ip_publico" {
  description = "IP fixo da instância."
  value       = aws_eip.assistente.public_ip
}

output "endereco" {
  description = "Endereço do assistente."
  value       = "https://${aws_route53_record.assistente.name}"
}

output "conectar" {
  description = "Comando para abrir o terminal na instância."
  value       = "aws ssm start-session --target ${aws_instance.assistente.id} --region ${var.regiao} --profile selvs"
}
