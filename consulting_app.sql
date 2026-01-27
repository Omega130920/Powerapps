-- MySQL dump 10.13  Distrib 8.0.43, for Win64 (x86_64)
--
-- Host: localhost    Database: consulting_app
-- ------------------------------------------------------
-- Server version	8.0.43

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',2,'add_permission'),(6,'Can change permission',2,'change_permission'),(7,'Can delete permission',2,'delete_permission'),(8,'Can view permission',2,'view_permission'),(9,'Can add group',3,'add_group'),(10,'Can change group',3,'change_group'),(11,'Can delete group',3,'delete_group'),(12,'Can view group',3,'view_group'),(13,'Can add user',4,'add_user'),(14,'Can change user',4,'change_user'),(15,'Can delete user',4,'delete_user'),(16,'Can view user',4,'view_user'),(17,'Can add content type',5,'add_contenttype'),(18,'Can change content type',5,'change_contenttype'),(19,'Can delete content type',5,'delete_contenttype'),(20,'Can view content type',5,'view_contenttype'),(21,'Can add session',6,'add_session'),(22,'Can change session',6,'change_session'),(23,'Can delete session',6,'delete_session'),(24,'Can view session',6,'view_session');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user`
--

DROP TABLE IF EXISTS `auth_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user`
--

LOCK TABLES `auth_user` WRITE;
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
INSERT INTO `auth_user` VALUES (1,'pbkdf2_sha256$1000000$jAUAN9GxmDLqK3EwdHo7Yg$DkNOr4kaYcwmI12Or3wviVMjPgP81v//f6GNqY7OAUk=','2026-01-05 13:45:16.688525',1,'omega','','','',1,1,'2026-01-05 13:30:36.359172');
/*!40000 ALTER TABLE `auth_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_groups`
--

DROP TABLE IF EXISTS `auth_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`),
  CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_groups`
--

LOCK TABLES `auth_user_groups` WRITE;
/*!40000 ALTER TABLE `auth_user_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_user_permissions`
--

DROP TABLE IF EXISTS `auth_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_user_permissions`
--

LOCK TABLES `auth_user_user_permissions` WRITE;
/*!40000 ALTER TABLE `auth_user_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `claims_claims`
--

DROP TABLE IF EXISTS `claims_claims`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `claims_claims` (
  `id` int NOT NULL AUTO_INCREMENT,
  `member_no` varchar(20) NOT NULL,
  `first_name` varchar(100) NOT NULL,
  `surname` varchar(100) NOT NULL,
  `id_passport` varchar(50) NOT NULL,
  `employer_code` varchar(50) NOT NULL,
  `employer_name` varchar(255) NOT NULL,
  `insurer` varchar(100) NOT NULL,
  `claim_type` varchar(100) NOT NULL,
  `consultant` varchar(100) NOT NULL,
  `last_action` varchar(255) DEFAULT 'Initial Submission',
  `status` varchar(20) DEFAULT 'Pending',
  `created_date` date NOT NULL,
  `initial_notes` text,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `claims_claims`
--

LOCK TABLES `claims_claims` WRITE;
/*!40000 ALTER TABLE `claims_claims` DISABLE KEYS */;
INSERT INTO `claims_claims` VALUES (1,'dsgs','sdgsdgs','sdgsdgs','sgdgsd','sdgsdgs','sgsgsd','Alan Gray','Funeral - main member','Stephan de Waal','Initial Submission','Pending','2025-12-08','');
/*!40000 ALTER TABLE `claims_claims` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `claimsnotes`
--

DROP TABLE IF EXISTS `claimsnotes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `claimsnotes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `claim_id` int NOT NULL,
  `communication_type` varchar(50) NOT NULL,
  `note_selection` varchar(100) NOT NULL,
  `note_body` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `created_by` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `myapp_claimsnotes_claim_id_idx` (`claim_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `claimsnotes`
--

LOCK TABLES `claimsnotes` WRITE;
/*!40000 ALTER TABLE `claimsnotes` DISABLE KEYS */;
INSERT INTO `claimsnotes` VALUES (1,1,'Inbound Call','Employer Follow-up','sf','2025-12-08 09:22:45.822203','System User');
/*!40000 ALTER TABLE `claimsnotes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `client_client`
--

DROP TABLE IF EXISTS `client_client`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `client_client` (
  `id` int NOT NULL AUTO_INCREMENT,
  `future_client_number` varchar(10) NOT NULL,
  `consultant` varchar(50) NOT NULL,
  `industry` varchar(50) DEFAULT NULL,
  `status` varchar(50) NOT NULL,
  `date_added` date DEFAULT NULL,
  `years_active` int DEFAULT NULL,
  `employees` int DEFAULT NULL,
  `product` varchar(50) DEFAULT NULL,
  `third_party_contract` tinyint(1) DEFAULT '0',
  `third_party_contact` varchar(50) DEFAULT NULL,
  `administrator` varchar(50) DEFAULT NULL,
  `umbrella_fund` varchar(50) DEFAULT NULL,
  `insurer` varchar(50) DEFAULT NULL,
  `assets` text,
  `consulting_letter_status` tinyint(1) DEFAULT '0',
  `consulting_letter_file` varchar(255) DEFAULT NULL,
  `sla_status` tinyint(1) DEFAULT '0',
  `sla_file` varchar(255) DEFAULT NULL,
  `third_party_doc_status` tinyint(1) DEFAULT '0',
  `third_party_doc_file` varchar(255) DEFAULT NULL,
  `fica_dd_completed` decimal(5,2) DEFAULT '0.00',
  `bulk_email_status` tinyint(1) DEFAULT '0',
  `client_name` varchar(255) DEFAULT NULL,
  `nature_of_relationship` varchar(100) DEFAULT 'Employer / Pension Fund',
  `purpose_of_relationship` varchar(100) DEFAULT 'Employee Pension Fund',
  `source_of_funds` varchar(100) DEFAULT 'Payroll',
  `due_diligence_form_name` varchar(255) DEFAULT NULL,
  `declaration_name` varchar(100) DEFAULT NULL,
  `declaration_delegation` varchar(100) DEFAULT NULL,
  `declaration_date` date DEFAULT NULL,
  `signed_form_upload` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `future_client_number` (`future_client_number`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `client_client`
--

LOCK TABLES `client_client` WRITE;
/*!40000 ALTER TABLE `client_client` DISABLE KEYS */;
INSERT INTO `client_client` VALUES (1,'FUT00001','','','','2025-11-10',2,1,'Individual Client',0,'Services','Sanlam','SUF Standard','Sanlam','N/A',0,NULL,0,NULL,0,NULL,0.00,0,'NEWNEW','Employer / Pension Fund','Employee Pension Fund','Payroll','','','',NULL,NULL),(6,'FUT00002','Marida Botha','Logistics','Active','2025-11-10',10,200,'Individual Client',0,'PMG','Sanlam','SUF Standard','Sanlam','',0,NULL,0,NULL,0,NULL,0.00,0,'Re-Find Market','Employer / Pension Fund','Employee Pension Fund','Payroll','','','',NULL,NULL),(7,'FUT00003','Awie de Swardt','Agricultural','Active','2025-11-10',10,200,'',0,'PMG','Sanlam','SUF Standard','Sanlam','',0,NULL,0,NULL,0,NULL,0.00,0,'Re-Find Market','Employer / Pension Fund','Employee Pension Fund','Payroll','','','',NULL,NULL),(8,'FUT00004','','','','2025-11-10',10,1,'',0,'','','','','',1,NULL,0,NULL,0,NULL,0.00,0,'ajkl','Employer / Pension Fund','Employee Pension Fund','Payroll','','','',NULL,NULL),(9,'FUT00005','Marida Botha','Retail','Active','2025-11-10',1,1,'',0,'','','','','',0,NULL,0,NULL,0,NULL,0.00,0,'qwertyuiop','Employer / Pension Fund','Employee Pension Fund','Payroll','','','',NULL,NULL),(10,'FUT00006','','Agricultural','Active','2025-11-10',1,1,'Individual Client',0,'Services','Sanlam','SUF Standard','Sanlam','',0,NULL,1,NULL,0,NULL,0.00,0,'Phase 3 ','Employer / Pension Fund','Employee Pension Fund','Payroll','','','',NULL,NULL),(11,'FUT00007','','Logistics','Active','2025-11-10',1,1,'',0,'','','','','',0,NULL,0,NULL,0,NULL,0.00,0,'ZeroSpark','Employer / Pension Fund','Employee Pension Fund','Payroll','','','',NULL,NULL);
/*!40000 ALTER TABLE `client_client` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `client_contact`
--

DROP TABLE IF EXISTS `client_contact`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `client_contact` (
  `id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `name` varchar(100) DEFAULT NULL,
  `surname` varchar(100) DEFAULT NULL,
  `job_title` varchar(100) DEFAULT NULL,
  `landline` varchar(50) DEFAULT NULL,
  `cell_no` varchar(50) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `physical_address` text,
  `postal_address` text,
  `city_town` varchar(50) DEFAULT NULL,
  `province` varchar(50) DEFAULT NULL,
  `birthday` varchar(50) DEFAULT NULL,
  `notes` text,
  `interests` text,
  PRIMARY KEY (`id`),
  KEY `client_id` (`client_id`),
  CONSTRAINT `client_contact_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `client_client` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `client_contact`
--

LOCK TABLES `client_contact` WRITE;
/*!40000 ALTER TABLE `client_contact` DISABLE KEYS */;
INSERT INTO `client_contact` VALUES (2,9,'luano','','','','','luanoveck@gmail.com','','','','','','',''),(13,10,'luano','','','','','luanoveck@gmail.com','','','','','','','');
/*!40000 ALTER TABLE `client_contact` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `client_list`
--

DROP TABLE IF EXISTS `client_list`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `client_list` (
  `scheme_code` varchar(225) DEFAULT NULL,
  `client_ref_no_2` varchar(225) DEFAULT NULL,
  `client_name` varchar(225) DEFAULT NULL,
  `consultant` varchar(225) DEFAULT NULL,
  `administrator` varchar(225) DEFAULT NULL,
  `umbrella_fund_option` varchar(225) DEFAULT NULL,
  `fica_dd_completed` varchar(225) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `client_list`
--

LOCK TABLES `client_list` WRITE;
/*!40000 ALTER TABLE `client_list` DISABLE KEYS */;
/*!40000 ALTER TABLE `client_list` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `client_reminders`
--

DROP TABLE IF EXISTS `client_reminders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `client_reminders` (
  `id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `title` varchar(200) NOT NULL,
  `note` text NOT NULL,
  `reminder_date` date NOT NULL,
  `created_by_id` int NOT NULL,
  `is_dismissed` tinyint(1) NOT NULL DEFAULT '0',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_reminders_client` (`client_id`),
  KEY `fk_reminders_user` (`created_by_id`),
  CONSTRAINT `fk_reminders_client` FOREIGN KEY (`client_id`) REFERENCES `client_client` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_reminders_user` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `client_reminders`
--

LOCK TABLES `client_reminders` WRITE;
/*!40000 ALTER TABLE `client_reminders` DISABLE KEYS */;
INSERT INTO `client_reminders` VALUES (1,1,'sdg','adsf','2026-01-05',1,1,'2026-01-05 13:32:51'),(2,1,'asf','sdf','2026-01-05',1,1,'2026-01-05 13:33:05'),(3,1,'Birthday','Birtday','2026-01-06',1,0,'2026-01-05 13:36:20'),(4,1,'Bath day','Taking the bath','2026-01-05',1,1,'2026-01-05 13:44:38');
/*!40000 ALTER TABLE `client_reminders` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `consulting_lead`
--

DROP TABLE IF EXISTS `consulting_lead`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `consulting_lead` (
  `id` int NOT NULL AUTO_INCREMENT,
  `lead_received_from` varchar(100) NOT NULL,
  `date_received` date NOT NULL,
  `company_name` varchar(255) NOT NULL,
  `contact_person` varchar(255) NOT NULL,
  `contact_number` varchar(50) DEFAULT NULL,
  `contact_email` varchar(254) DEFAULT NULL,
  `product_required` varchar(100) NOT NULL,
  `status` varchar(20) NOT NULL DEFAULT 'New',
  `assigned_to` varchar(100) DEFAULT NULL,
  `date_accepted` date DEFAULT NULL,
  `start_date` date DEFAULT NULL,
  `last_follow_up` date DEFAULT NULL,
  `internal_notes` text,
  `communication_type` varchar(50) DEFAULT NULL,
  `note_type` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `consulting_lead`
--

LOCK TABLES `consulting_lead` WRITE;
/*!40000 ALTER TABLE `consulting_lead` DISABLE KEYS */;
INSERT INTO `consulting_lead` VALUES (2,'golf day','2025-12-08','Luano','Omega Omega','0833803942','luanoveck@gmail.com','Health Care','New','MARIDA BOTHA',NULL,NULL,'2025-12-08','\n\n--- LOGGED: 2025-12-08 10:04 ---\nCOMM TYPE: Email\nNOTE TYPE: Proposal\nSELECTION: N/A\nPOSTED BY: MARIDA BOTHA\nNOTES:\nfg','email','proposal'),(3,'golf day','2025-12-08','Omega','Omega Omega','0833803942','luanoveck@gmail.com','Individual Client','New','MERRIL FENNESSY',NULL,NULL,'2025-12-08','',NULL,NULL);
/*!40000 ALTER TABLE `consulting_lead` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (1,'admin','logentry'),(3,'auth','group'),(2,'auth','permission'),(4,'auth','user'),(5,'contenttypes','contenttype'),(6,'sessions','session');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2025-12-08 09:21:00.958562'),(2,'auth','0001_initial','2025-12-08 09:21:01.395495'),(3,'admin','0001_initial','2025-12-08 09:21:01.519461'),(4,'admin','0002_logentry_remove_auto_add','2025-12-08 09:21:01.525068'),(5,'admin','0003_logentry_add_action_flag_choices','2025-12-08 09:21:01.531192'),(6,'contenttypes','0002_remove_content_type_name','2025-12-08 09:21:01.617274'),(7,'auth','0002_alter_permission_name_max_length','2025-12-08 09:21:01.669426'),(8,'auth','0003_alter_user_email_max_length','2025-12-08 09:21:01.695746'),(9,'auth','0004_alter_user_username_opts','2025-12-08 09:21:01.702801'),(10,'auth','0005_alter_user_last_login_null','2025-12-08 09:21:01.764659'),(11,'auth','0006_require_contenttypes_0002','2025-12-08 09:21:01.767193'),(12,'auth','0007_alter_validators_add_error_messages','2025-12-08 09:21:01.771941'),(13,'auth','0008_alter_user_username_max_length','2025-12-08 09:21:01.832355'),(14,'auth','0009_alter_user_last_name_max_length','2025-12-08 09:21:01.903587'),(15,'auth','0010_alter_group_name_max_length','2025-12-08 09:21:01.921204'),(16,'auth','0011_update_proxy_permissions','2025-12-08 09:21:01.928614'),(17,'auth','0012_alter_user_first_name_max_length','2025-12-08 09:21:01.988487'),(18,'sessions','0001_initial','2025-12-08 09:21:02.021770');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
INSERT INTO `django_session` VALUES ('1h9axng1gf4psva8r45h961zvbor89xu','.eJxVjEEOwiAQRe_C2hCGUigu3XsGMjCDVA0kpV0Z765NutDtf-_9lwi4rSVsnZcwkzgLEKffLWJ6cN0B3bHemkytrssc5a7Ig3Z5bcTPy-H-HRTs5VtrYsoeDWrOGDV452gwahytY0gxG7aUlWM2NgJZpGECQx4BJwOKSLw_Cx44uQ:1vcktY:D4KpuCr-d-k-SHuT7zPUzavxuCiNVYic_AEY5eBT9B8','2026-01-19 13:45:16.700519');
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `fica_address`
--

DROP TABLE IF EXISTS `fica_address`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fica_address` (
  `id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `address_type` varchar(20) NOT NULL,
  `line1` varchar(150) NOT NULL,
  `line2` varchar(150) DEFAULT NULL,
  `province` varchar(50) DEFAULT NULL,
  `city` varchar(100) DEFAULT NULL,
  `suburb` varchar(100) DEFAULT NULL,
  `postal_code` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `client_id` (`client_id`),
  CONSTRAINT `fica_address_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `client_client` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `fica_address`
--

LOCK TABLES `fica_address` WRITE;
/*!40000 ALTER TABLE `fica_address` DISABLE KEYS */;
INSERT INTO `fica_address` VALUES (1,1,'physical','','','','','',''),(5,6,'physical','44 Minuet Ridge','','Western Cape','Cape Town','Durbanville','7440'),(6,7,'physical','','','','','',''),(7,8,'physical','','','','','',''),(8,9,'physical','','','','','',''),(9,10,'physical','44 Minuet Ridge','','Western Cape','Cape Town','Durbanville','7440'),(10,11,'physical','','','','','','');
/*!40000 ALTER TABLE `fica_address` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `fica_beneficialowner`
--

DROP TABLE IF EXISTS `fica_beneficialowner`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fica_beneficialowner` (
  `id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `name` varchar(100) NOT NULL,
  `surname` varchar(100) DEFAULT NULL,
  `designation` varchar(100) DEFAULT NULL,
  `id_number` varchar(50) NOT NULL,
  `contact_number` varchar(50) DEFAULT NULL,
  `email_address` varchar(100) DEFAULT NULL,
  `phys_line1` varchar(150) NOT NULL,
  `phys_line2` varchar(150) DEFAULT NULL,
  `phys_province` varchar(50) DEFAULT NULL,
  `phys_city` varchar(100) DEFAULT NULL,
  `phys_suburb` varchar(100) DEFAULT NULL,
  `phys_code` varchar(20) DEFAULT NULL,
  `postal_same_as_phys` tinyint(1) DEFAULT '1',
  `postal_line1` varchar(150) DEFAULT NULL,
  `postal_line2` varchar(150) DEFAULT NULL,
  `postal_province` varchar(50) DEFAULT NULL,
  `proof_addr_file` varchar(255) DEFAULT NULL,
  `id_copy_file` varchar(255) DEFAULT NULL,
  `is_pep` tinyint(1) DEFAULT '0',
  `pep_reason` text,
  `is_pip` tinyint(1) DEFAULT '0',
  `pip_reason` text,
  `is_ppo` tinyint(1) DEFAULT '0',
  `ppo_reason` text,
  `is_kca` tinyint(1) DEFAULT '0',
  `kca_reason` text,
  PRIMARY KEY (`id`),
  KEY `client_id` (`client_id`),
  CONSTRAINT `fica_beneficialowner_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `client_client` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `fica_beneficialowner`
--

LOCK TABLES `fica_beneficialowner` WRITE;
/*!40000 ALTER TABLE `fica_beneficialowner` DISABLE KEYS */;
/*!40000 ALTER TABLE `fica_beneficialowner` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `fica_director`
--

DROP TABLE IF EXISTS `fica_director`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fica_director` (
  `id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `name` varchar(100) NOT NULL,
  `surname` varchar(100) DEFAULT NULL,
  `designation` varchar(100) DEFAULT NULL,
  `id_number` varchar(50) NOT NULL,
  `contact_number` varchar(50) DEFAULT NULL,
  `email_address` varchar(100) DEFAULT NULL,
  `phys_line1` varchar(150) NOT NULL,
  `phys_line2` varchar(150) DEFAULT NULL,
  `phys_province` varchar(50) DEFAULT NULL,
  `phys_city` varchar(100) DEFAULT NULL,
  `phys_suburb` varchar(100) DEFAULT NULL,
  `phys_code` varchar(20) DEFAULT NULL,
  `postal_same_as_phys` tinyint(1) DEFAULT '1',
  `postal_line1` varchar(150) DEFAULT NULL,
  `postal_line2` varchar(150) DEFAULT NULL,
  `postal_province` varchar(50) DEFAULT NULL,
  `proof_addr_file` varchar(255) DEFAULT NULL,
  `id_copy_file` varchar(255) DEFAULT NULL,
  `is_pep` tinyint(1) DEFAULT '0',
  `pep_reason` text,
  `is_pip` tinyint(1) DEFAULT '0',
  `pip_reason` text,
  `is_ppo` tinyint(1) DEFAULT '0',
  `ppo_reason` text,
  `is_kca` tinyint(1) DEFAULT '0',
  `kca_reason` text,
  PRIMARY KEY (`id`),
  KEY `client_id` (`client_id`),
  CONSTRAINT `fica_director_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `client_client` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `fica_director`
--

LOCK TABLES `fica_director` WRITE;
/*!40000 ALTER TABLE `fica_director` DISABLE KEYS */;
INSERT INTO `fica_director` VALUES (1,6,'luano','van Eck','','','0833803942','luanoveck@gmail.com','44 Minuet Ridge','','','Cape Town','','7440',1,NULL,NULL,NULL,NULL,NULL,0,NULL,0,NULL,0,NULL,0,NULL);
/*!40000 ALTER TABLE `fica_director` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `fica_responsibleperson`
--

DROP TABLE IF EXISTS `fica_responsibleperson`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fica_responsibleperson` (
  `id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `name` varchar(100) NOT NULL,
  `surname` varchar(100) DEFAULT NULL,
  `designation` varchar(100) DEFAULT NULL,
  `id_number` varchar(50) NOT NULL,
  `contact_number` varchar(50) DEFAULT NULL,
  `email_address` varchar(100) DEFAULT NULL,
  `resp_line1` varchar(150) DEFAULT NULL,
  `resp_line2` varchar(150) DEFAULT NULL,
  `resp_province` varchar(50) DEFAULT NULL,
  `resp_city` varchar(100) DEFAULT NULL,
  `resp_suburb` varchar(100) DEFAULT NULL,
  `resp_code` varchar(20) DEFAULT NULL,
  `circular_upload_file` varchar(255) DEFAULT NULL,
  `doc_signed_upload_file` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `client_id` (`client_id`),
  CONSTRAINT `fica_responsibleperson_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `client_client` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `fica_responsibleperson`
--

LOCK TABLES `fica_responsibleperson` WRITE;
/*!40000 ALTER TABLE `fica_responsibleperson` DISABLE KEYS */;
INSERT INTO `fica_responsibleperson` VALUES (2,6,'luano','van Eck','','','0833803942','luanoveck@gmail.com','44 Minuet Ridge','','','Cape Town','','7440',NULL,NULL);
/*!40000 ALTER TABLE `fica_responsibleperson` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `reminders`
--

DROP TABLE IF EXISTS `reminders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `reminders` (
  `id` int NOT NULL AUTO_INCREMENT,
  `claim_id` int NOT NULL,
  `member_no` varchar(50) NOT NULL,
  `reminder_date` date NOT NULL,
  `recipient_emails` text NOT NULL,
  `reminder_note` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `created_by` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `reminders_claim_id_idx` (`claim_id`),
  KEY `reminders_member_no_idx` (`member_no`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `reminders`
--

LOCK TABLES `reminders` WRITE;
/*!40000 ALTER TABLE `reminders` DISABLE KEYS */;
INSERT INTO `reminders` VALUES (1,1,'dsgs','2025-12-08','consultant.email@example.com','dfgsda','2025-12-08 10:02:24.769517','Consultant (Placeholder)'),(2,1,'dsgs','2025-12-09','consultant.email@example.com','Hello','2025-12-08 11:46:13.843143','Consultant (Placeholder)');
/*!40000 ALTER TABLE `reminders` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-01-27 10:38:12
