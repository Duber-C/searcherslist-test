##############################################################################
# DB Subnet Group (requires at least 2 AZs)
##############################################################################

resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-${var.environment}-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id

  tags = { Name = "${var.project_name}-${var.environment}-db-subnet-group" }
}

##############################################################################
# RDS PostgreSQL Instance
##############################################################################

resource "aws_db_instance" "postgres" {
  identifier        = "${var.project_name}-${var.environment}-db"
  engine            = "postgres"
  engine_version    = "18"
  instance_class    = var.db_instance_class
  allocated_storage = var.db_allocated_storage
  storage_type      = "gp3"
  storage_encrypted = true

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  multi_az                  = var.db_multi_az
  publicly_accessible       = var.rds_publicly_accessible
  deletion_protection       = false
  skip_final_snapshot       = true
  final_snapshot_identifier = "${var.project_name}-${var.environment}-final-snapshot"

  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:04:00-sun:05:00"

  tags = { Name = "${var.project_name}-${var.environment}-db" }
}
