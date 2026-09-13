# Rede de proteção contra esquecer a máquina ligada: se a CPU ficar abaixo
# de 5% pelo tempo configurado, o alarme desliga a instância sozinho.
resource "aws_cloudwatch_metric_alarm" "ociosidade" {
  alarm_name          = "${var.nome}-ociosa"
  alarm_description   = "Desliga a instância após ${var.minutos_ociosidade} min de CPU baixa"
  namespace           = "AWS/EC2"
  metric_name         = "CPUUtilization"
  statistic           = "Average"
  period              = 300
  evaluation_periods  = ceil(var.minutos_ociosidade / 5)
  threshold           = 5
  comparison_operator = "LessThanThreshold"
  treat_missing_data  = "notBreaching"

  dimensions = { InstanceId = aws_instance.assistente.id }

  alarm_actions = ["arn:aws:automate:${var.regiao}:ec2:stop"]
}
