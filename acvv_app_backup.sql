-- MySQL dump 10.13  Distrib 8.0.43, for Win64 (x86_64)
--
-- Host: localhost    Database: acvv_app
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
-- Table structure for table `acvv_claim_notes`
--

DROP TABLE IF EXISTS `acvv_claim_notes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `acvv_claim_notes` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `claim_id` int NOT NULL,
  `note_selection` varchar(255) DEFAULT NULL,
  `note_description` text,
  `attachment` varchar(255) DEFAULT NULL,
  `created_at` datetime NOT NULL,
  `created_by_id` int DEFAULT NULL,
  PRIMARY KEY (`ID`),
  KEY `fk_claim_notes_claim` (`claim_id`),
  KEY `fk_claim_notes_user` (`created_by_id`),
  CONSTRAINT `fk_claim_notes_claim` FOREIGN KEY (`claim_id`) REFERENCES `acvv_claims` (`ID`) ON DELETE CASCADE,
  CONSTRAINT `fk_claim_notes_user` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `acvv_claim_notes`
--

LOCK TABLES `acvv_claim_notes` WRITE;
/*!40000 ALTER TABLE `acvv_claim_notes` DISABLE KEYS */;
/*!40000 ALTER TABLE `acvv_claim_notes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acvv_claims`
--

DROP TABLE IF EXISTS `acvv_claims`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `acvv_claims` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `company_code` varchar(50) NOT NULL,
  `agent` varchar(100) DEFAULT NULL,
  `id_number` varchar(50) NOT NULL,
  `member_name` varchar(255) NOT NULL,
  `member_surname` varchar(255) NOT NULL,
  `mip_number` varchar(50) DEFAULT NULL,
  `claim_type` varchar(100) NOT NULL,
  `exit_reason` varchar(100) DEFAULT NULL,
  `claim_status` varchar(100) NOT NULL,
  `payment_option` varchar(100) DEFAULT NULL,
  `claim_allocation` varchar(100) NOT NULL,
  `claim_amount` decimal(15,2) DEFAULT NULL,
  `claim_created_date` date DEFAULT NULL,
  `last_contribution_date` date DEFAULT NULL,
  `date_submitted` date DEFAULT NULL,
  `date_paid` date DEFAULT NULL,
  `vested_pot_available` tinyint(1) DEFAULT '0',
  `savings_pot_available` tinyint(1) DEFAULT '0',
  `vested_pot_paid_date` date DEFAULT NULL,
  `savings_pot_paid_date` date DEFAULT NULL,
  `infund_cert_date` date DEFAULT NULL,
  `linked_email_id` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `acvv_claims`
--

LOCK TABLES `acvv_claims` WRITE;
/*!40000 ALTER TABLE `acvv_claims` DISABLE KEYS */;
/*!40000 ALTER TABLE `acvv_claims` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `acvv_outlook_token`
--

DROP TABLE IF EXISTS `acvv_outlook_token`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `acvv_outlook_token` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_principal_name` varchar(255) NOT NULL,
  `access_token` longtext NOT NULL,
  `refresh_token` longtext,
  `expires_in_seconds` int NOT NULL DEFAULT '3600',
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_principal_name` (`user_principal_name`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `acvv_outlook_token`
--

LOCK TABLES `acvv_outlook_token` WRITE;
/*!40000 ALTER TABLE `acvv_outlook_token` DISABLE KEYS */;
INSERT INTO `acvv_outlook_token` VALUES (1,'testuser@futurasa.co.za','eyJ0eXAiOiJKV1QiLCJub25jZSI6Ik1hcWY1TnQyWU1GQTVFSjlqM0NZdzl5cWhNdjhtSE82cE9YZVdHN3BZV3ciLCJhbGciOiJSUzI1NiIsIng1dCI6IlBjWDk4R1g0MjBUMVg2c0JEa3poUW1xZ3dNVSIsImtpZCI6IlBjWDk4R1g0MjBUMVg2c0JEa3poUW1xZ3dNVSJ9.eyJhdWQiOiJodHRwczovL2dyYXBoLm1pY3Jvc29mdC5jb20iLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC83YmNmYzA4MC1lMWYxLTRmOTktYjRlZC1lMWE5NmVkYTg5Y2UvIiwiaWF0IjoxNzY4OTEzMDExLCJuYmYiOjE3Njg5MTMwMTEsImV4cCI6MTc2ODkxNjkxMSwiYWlvIjoiazJaZ1lCRGNlQ2xpbXR1dFJaRTN2cWtLekRtVkNRQT0iLCJhcHBfZGlzcGxheW5hbWUiOiJGdXR1cmEtQXBwIiwiYXBwaWQiOiI5ZjgyZTU3ZC00NWE0LTRiNjYtYWIyOS04YTliMzgxYTA4MmEiLCJhcHBpZGFjciI6IjEiLCJpZHAiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC83YmNmYzA4MC1lMWYxLTRmOTktYjRlZC1lMWE5NmVkYTg5Y2UvIiwiaWR0eXAiOiJhcHAiLCJvaWQiOiI0MTc2NDgyNy0yZGJlLTRiMTYtYWJhNi0xZDIwMDYxYjU5MWYiLCJyaCI6IjEuQVNBQWdNRFBlX0hobVUtMDdlR3BidHFKemdNQUFBQUFBQUFBd0FBQUFBQUFBQUE5QVFBZ0FBLiIsInJvbGVzIjpbIk1haWwuUmVhZCIsIk1haWwuU2VuZCJdLCJzdWIiOiI0MTc2NDgyNy0yZGJlLTRiMTYtYWJhNi0xZDIwMDYxYjU5MWYiLCJ0ZW5hbnRfcmVnaW9uX3Njb3BlIjoiQUYiLCJ0aWQiOiI3YmNmYzA4MC1lMWYxLTRmOTktYjRlZC1lMWE5NmVkYTg5Y2UiLCJ1dGkiOiI3SGdrZE0xbUMweWp6ZkNIOGFFdEFBIiwidmVyIjoiMS4wIiwid2lkcyI6WyIwOTk3YTFkMC0wZDFkLTRhY2ItYjQwOC1kNWNhNzMxMjFlOTAiXSwieG1zX2FjZCI6MTc2NDE2MDkyNiwieG1zX2FjdF9mY3QiOiIzIDkiLCJ4bXNfZnRkIjoid2xUUzJIWjR0NF9ZQUJjRFpiZ1JfZXJJc2tCR3dwZGl4alhOUWJpc25nWUJaWFZ5YjNCbGJtOXlkR2d0WkhOdGN3IiwieG1zX2lkcmVsIjoiMjggNyIsInhtc19yZCI6IjAuNDJMbFlCSmlWQkFTNFdBWEV2aFM4X2Ria2R4T3g1bF9jajdPVU42bUJ4VGxGQko0MjVBY0Z0TFQ3RDVkZ2VGMVdWbXRMMUNVUTBpQW1RRUNEa0JwQUEiLCJ4bXNfc3ViX2ZjdCI6IjkgMyIsInhtc190Y2R0IjoxNDk5NzEyNDIwLCJ4bXNfdG50X2ZjdCI6IjYgMyJ9.RUhxK2cGvOfpKRRlTDiJZQIY5fwydqbJjxuzXfKpxXrmxS0pVWh-jpC-RI0yGnxI1J6g5IljNzrdSO6lX9vuB357zwb5FEKPifTJmQh6_1Eb2yuFyUbRJ0s5PjhbNFjOceoE7a1m5R5QwqAAbujZmam20Hh8ahIbiFzkW104B143sbbTcVKG-HsCUM7lggRWEygCZnndZ9U4bbiVconaxdf9wiPAeQ08mXRJWY-uXiYeYfvMzGf2KtGqKUSf2YzVS8xxlObhBPjA8l8hlhpO6sKwZKL3EQE87Pjvw6M7qRkv5xIoI0NST4VIKo0J8BStBYm4hDlM8fCoZgQErqORxw',NULL,3599,'2026-01-20 12:48:31.840171');
/*!40000 ALTER TABLE `acvv_outlook_token` ENABLE KEYS */;
UNLOCK TABLES;

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
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user`
--

LOCK TABLES `auth_user` WRITE;
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
INSERT INTO `auth_user` VALUES (1,'pbkdf2_sha256$1000000$0zg9UjZB2zeXSXInM9C3Md$igTZw8J2jh3znUITqGVLWa7Rnm0XOjrpqtc21GO/uQs=','2026-01-20 12:35:56.623736',1,'omega','','','',1,1,'2025-09-19 11:24:27.343696'),(2,'pbkdf2_sha256$1000000$dmFBjFd3XWtYQDePDKE1qQ$VbHMeUILJFaR9aZ7eTTIm3qpJmz2ixVbAlv+hbMLrNA=','2025-12-11 09:31:18.620642',0,'testuser','','','test@example.com',0,1,'2025-12-11 08:24:58.760332'),(3,'pbkdf2_sha256$1000000$A6jOIWZeJPKi5HOwLb1Lxv$bjhJFbJALlW79g9YGYS9xhIDlHvbo0DsAGglo9TlvRY=','2026-01-13 13:29:07.379898',0,'testuser1','','','',0,1,'2025-12-17 09:59:07.678369'),(4,'pbkdf2_sha256$1000000$7SPlHWZzImqF6bgXpBsmQf$JAfm9A/lxtXqSjfM/oU/o8yeZ264hgAqzS+VzhUOvCI=',NULL,0,'testuser2','','','',0,1,'2025-12-17 09:59:08.012316'),(5,'pbkdf2_sha256$1000000$VuhW8ZRFtGZyuKEXYsom32$6DFdB0pUijLFEZ3xbOBy/ROb4tKl0Z+4MDPulqVzPhM=',NULL,0,'testuser3','','','',0,1,'2025-12-17 09:59:08.337488'),(6,'pbkdf2_sha256$1000000$OBszZ7dhhdPgkL7xuTC2h3$dw2k2ERlcYoHZRZvUNsRrizQGT7XAI+FiHpdafrNK1Q=',NULL,0,'testuser4','','','',0,1,'2025-12-17 09:59:08.662876');
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
-- Table structure for table `branch_documents`
--

DROP TABLE IF EXISTS `branch_documents`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `branch_documents` (
  `id` int NOT NULL AUTO_INCREMENT,
  `branch_name` varchar(255) NOT NULL,
  `file_name` varchar(255) NOT NULL,
  `file_path` varchar(500) NOT NULL,
  `uploaded_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `uploaded_by` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `branch_documents`
--

LOCK TABLES `branch_documents` WRITE;
/*!40000 ALTER TABLE `branch_documents` DISABLE KEYS */;
/*!40000 ALTER TABLE `branch_documents` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `client_notes`
--

DROP TABLE IF EXISTS `client_notes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `client_notes` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `MIP Names` text,
  `date` datetime DEFAULT NULL,
  `User` text,
  `notes` text,
  `communication_type` varchar(100) DEFAULT NULL,
  `action_note_type` varchar(100) DEFAULT NULL,
  `attachment` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `client_notes`
--

LOCK TABLES `client_notes` WRITE;
/*!40000 ALTER TABLE `client_notes` DISABLE KEYS */;
INSERT INTO `client_notes` VALUES (1,'Koos','2025-09-23 00:00:00','Roos','I want to Mr.Koos a Roos',NULL,NULL,NULL),(2,'MGC001','2025-09-23 00:00:00','Roos','I want to buy Mr.Koos a Roos',NULL,NULL,NULL),(3,'MGC001','2025-09-23 10:57:52','omega','Hello Koos',NULL,NULL,NULL),(4,'ACVV Aberdeen (PF001)','2026-01-15 09:41:32','omega','Test','Incoming Call','Feedback to Member','');
/*!40000 ALTER TABLE `client_notes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `delegation_note`
--

DROP TABLE IF EXISTS `delegation_note`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `delegation_note` (
  `id` int NOT NULL AUTO_INCREMENT,
  `delegation_id` int NOT NULL,
  `user_id` int DEFAULT NULL,
  `content` text NOT NULL,
  `created_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `delegation_id` (`delegation_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `delegation_note_ibfk_1` FOREIGN KEY (`delegation_id`) REFERENCES `email_delegation` (`id`) ON DELETE CASCADE,
  CONSTRAINT `delegation_note_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `delegation_note`
--

LOCK TABLES `delegation_note` WRITE;
/*!40000 ALTER TABLE `delegation_note` DISABLE KEYS */;
INSERT INTO `delegation_note` VALUES (1,5,1,'Delegated to testuser. Category: , MIP: None','2025-12-11 08:30:55.995685'),(2,8,1,'Delegated to testuser. Category: LPI, MIP: None','2025-12-11 09:14:09.034607'),(3,31,1,'Delegated to testuser1. Category: Schedule, MIP: PF001','2026-01-13 11:30:21.684202'),(4,32,1,'Delegated to testuser1. Category: Claim, MIP: ACVV Aberdeen (PF001)','2026-01-13 11:43:07.388939');
/*!40000 ALTER TABLE `delegation_note` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `delegation_transaction_log`
--

DROP TABLE IF EXISTS `delegation_transaction_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `delegation_transaction_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `delegation_id` int NOT NULL,
  `user_id` int DEFAULT NULL,
  `subject` varchar(255) NOT NULL,
  `recipient_email` varchar(255) NOT NULL,
  `action_type` varchar(50) NOT NULL,
  `transaction_time` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `delegation_id` (`delegation_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `delegation_transaction_log_ibfk_1` FOREIGN KEY (`delegation_id`) REFERENCES `email_delegation` (`id`) ON DELETE CASCADE,
  CONSTRAINT `delegation_transaction_log_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `delegation_transaction_log`
--

LOCK TABLES `delegation_transaction_log` WRITE;
/*!40000 ALTER TABLE `delegation_transaction_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `delegation_transaction_log` ENABLE KEYS */;
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
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2025-09-19 11:23:41.681684'),(2,'auth','0001_initial','2025-09-19 11:23:43.231167'),(3,'admin','0001_initial','2025-09-19 11:23:43.589701'),(4,'admin','0002_logentry_remove_auto_add','2025-09-19 11:23:43.605393'),(5,'admin','0003_logentry_add_action_flag_choices','2025-09-19 11:23:43.623268'),(6,'contenttypes','0002_remove_content_type_name','2025-09-19 11:23:43.874121'),(7,'auth','0002_alter_permission_name_max_length','2025-09-19 11:23:44.029325'),(8,'auth','0003_alter_user_email_max_length','2025-09-19 11:23:44.088012'),(9,'auth','0004_alter_user_username_opts','2025-09-19 11:23:44.101939'),(10,'auth','0005_alter_user_last_login_null','2025-09-19 11:23:44.214890'),(11,'auth','0006_require_contenttypes_0002','2025-09-19 11:23:44.230632'),(12,'auth','0007_alter_validators_add_error_messages','2025-09-19 11:23:44.251585'),(13,'auth','0008_alter_user_username_max_length','2025-09-19 11:23:44.382657'),(14,'auth','0009_alter_user_last_name_max_length','2025-09-19 11:23:44.546081'),(15,'auth','0010_alter_group_name_max_length','2025-09-19 11:23:44.568372'),(16,'auth','0011_update_proxy_permissions','2025-09-19 11:23:44.588281'),(17,'auth','0012_alter_user_first_name_max_length','2025-09-19 11:23:44.747540'),(18,'sessions','0001_initial','2025-09-19 11:23:44.832849');
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
INSERT INTO `django_session` VALUES ('018qwmxfyz2tadifujxw32jbr2xdq22e','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1v0c12:DjtpoiIKLphnUVFzKC0tiW1E9hkxCUoRrWB5H89vcgk','2025-10-06 08:35:20.587529'),('2d9fjhdj825wf38ekhrvjb409r0e732c','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1v0fqL:2FyIHs5Le40E47vCzkPYoEvmn8hBjE5zPbrgXv8IK3o','2025-10-06 12:40:33.162859'),('2kb9wbxsis1qm9ekdf68hhbgmxjyvcgy','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vOcjg:vAkru7Z6gEo4aQ8h3D2c6aYCu09qKSw9fbhRfAmjr8Q','2025-12-11 14:12:40.542000'),('2ryh8ntcvu5wa5oqbtzgnlhyj54i2fwr','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1v1ibn:G8ikhiVtjwxWTg61pMWtrF_NZF1qcMChCXARzXSm_5Y','2025-10-09 09:49:51.511498'),('2u1xapmm8ky5d50zvhb208o5dmxsq4ti','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vWDNc:1L3gOxyD2eI-JPurhrcFzLLkC7Yc5LE2Me5QQeuLYOU','2026-01-01 12:45:16.693716'),('32mafyj110632k3okrl2qroai0nvka9b','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1v4FNz:cvj2_s4RMSAnZ6Qh_T8_0LlzZpjBc8Uwg_UoS0pnYcI','2025-10-16 09:14:03.408365'),('4pvaa7i9r6myclyrfr96thrp34fcnn0m','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1viAxg:vYO650t5TR-6LMyCux4sgE3XF0xozWUsFn-6rtMC-c0','2026-02-03 12:35:56.639035'),('4xbr8ql7tz59l7ai1as2p4vg03zltw5b','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1v0gmE:HwnFn3kixVObykipbhUzbVUeOSIFaZt4DdcyuuY4rmU','2025-10-06 13:40:22.320585'),('7fjpfeffsdxsc1s2dzoqsufzzdwvvdq7','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vSxQ8:CtS9xsPBwh9Txo9AaIziVwItG5Kgp2sEa2vR0bvrNMA','2025-12-23 13:06:24.768193'),('afd9eo10ao41mlqogjkz9lo3plhtt3ja','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vgHZD:bKAK8l1fdkjA6vIj1QHLsSaUYRoPLoavHW12hzEm8wo','2026-01-29 07:14:51.628953'),('ah29ugr3rjzbapna304dg56sizd9x0yv','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vfeTH:cuEpl-23cQbV70KjgWQXpGfJRK3IOqH1jVC4FOUkKYc','2026-01-27 13:30:07.907517'),('apeiyv097esg2dmaajdgqbkia26ic0nt','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1v0aqe:FpyzmyU0o9IoVUrFsxZBCooF0oyp2kyt0OCNkL6zRB0','2025-10-06 07:20:32.380066'),('dq5b08w0ntrcvn7y7470gznp6l0tzixw','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1v0xrk:Bqo8CuLED0d_ZlDP436cSojDNkm5SlbpJvhzIksBaXo','2025-10-07 07:55:12.318694'),('fpbvp5qlrfs8ygbpyal9ly6x07a4hmp2','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1v0zVK:OSishOOoLAFS_aNFM1okDciqibEqZvicCBvvjHBoo5M','2025-10-07 09:40:10.535461'),('hqvhhrwpbuw3dw152yp518naoa2zlij7','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vTPJ5:1I40ajLXJHOS2ukCbNdaAMyJ2kto5hloI_UCX8mQDXE','2025-12-24 18:52:59.836797'),('kiz2zhkcusp1k65kv6rsode2msfaumu6','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1v0dUE:doUpjmxx1WXqkkxLr8nv9eZgIYZbhmZI7blriWLNCjk','2025-10-06 10:09:34.546298'),('lycdf2q5duoakuhxghcc2hd7yn8x3ue9','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1v0gSJ:SRpDIBo029DoNWsKe-Q2W8nPFpKX_GpiA_1G6VhqT6U','2025-10-06 13:19:47.032976'),('pyap4iqiyseo70dnoxfm9hygswbe7sfh','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vU0Ji:wMJ49uYEZOf0_kWjkIY_ZAeju61yVJC5iest0AG4VSE','2025-12-26 10:24:06.124490'),('simb3r12rgyr8lyy6royse3u4c8qr3rq','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vTzdM:9wuzMlBa6bGyMvCvtZigtkHJZ09LVRZAmHkaIaqFOQ8','2025-12-26 09:40:20.342925'),('suy2xw9ouz532todnxfb8qofpqeqrqwe','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1v0xMf:MowAagjOHf8PBQDiMi6LLPerDuS2-njF8CdhH469F4o','2025-10-07 07:23:05.991425'),('up4qygzkowha3kmjfvsn7fs4ayvg94ej','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1v1lGF:wEqh0uEhgMqw1AG7dE-B9XRCi7QIXbs1Y27cSK4ypZM','2025-10-09 12:39:47.986746'),('us28ktm45qwazizmt1ezgiq5jldg8haf','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vSuYU:viUwCEgQcBfrWlUCEmAyiKRBTtguQMNW8Y5UpMCZd3s','2025-12-23 10:02:50.618457'),('vbfhssrrzxdojbouaupitr4wzgyw5p14','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1uzZWX:Brx_PkMem2FfqyDBvEaUYkLC_aEkvZa0xubReKj-JiQ','2025-10-03 11:43:33.944470'),('vqgiiuo4hmzbafwhy67zhgbi3rgycyyw','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vcgoT:UfcdBegDFUnqzmsrLp0yhP9OJ3VFxJ9IlO1JN5ObWnA','2026-01-19 09:23:45.574943'),('wdxr07t4ww8lhlxsq3zfrya6h7jhinbo','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vXg1t:AWaS4HbqUu9tceMip3fCjQmPxEx_csDZsmbOUU-ZGro','2026-01-05 13:32:53.341842'),('xr9f4th80uj5lcqhsr4nfo87oilfyidj','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vTdAO:R9TNTirEzApyVlMbaSiTAwk8bWaEJbyEUOL8CvPSq60','2025-12-25 09:40:56.210810'),('xsmr2wvie4xzgnjkdlh84lqmfj4191cf','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vfyUn:ns-sDMhRE7NKaduyFdXvi48zQH8o2eOgPr1AGE97Gb8','2026-01-28 10:53:01.904413'),('yx8jvink9m31cjtwqiu8noar6thiwynb','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vYIiK:g4vz4Ikqkd7oTnKFbelSAfHGQyuPe24Qt8_eeQzssYo','2026-01-07 06:51:16.361451'),('zl55fj2bpxd1xh4cqwvelod9smw8exkd','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vgIlc:OdDi9syjTmYSWvCJTPl0BGQ0yjkiWIqxn05O9IU4K80','2026-01-29 08:31:44.594953');
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `email_delegation`
--

DROP TABLE IF EXISTS `email_delegation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `email_delegation` (
  `id` int NOT NULL AUTO_INCREMENT,
  `email_id` varchar(255) NOT NULL,
  `subject` varchar(255) DEFAULT NULL,
  `sender_address` varchar(255) DEFAULT NULL,
  `assigned_user_id` int DEFAULT NULL,
  `status` varchar(10) NOT NULL,
  `delegated_at` datetime(6) DEFAULT NULL,
  `work_related` tinyint(1) NOT NULL DEFAULT '1',
  `email_category` varchar(50) DEFAULT NULL,
  `communication_type` varchar(50) DEFAULT NULL,
  `mip_names` varchar(50) DEFAULT NULL,
  `received_at` datetime(6) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email_id` (`email_id`),
  KEY `assigned_user_id` (`assigned_user_id`),
  CONSTRAINT `email_delegation_ibfk_1` FOREIGN KEY (`assigned_user_id`) REFERENCES `auth_user` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=33 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `email_delegation`
--

LOCK TABLES `email_delegation` WRITE;
/*!40000 ALTER TABLE `email_delegation` DISABLE KEYS */;
INSERT INTO `email_delegation` VALUES (1,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAIMinLAAA=','Testing 2','luano@futurasa.co.za',NULL,'NEW',NULL,1,NULL,NULL,NULL,NULL),(2,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAIMinKAAA=','Test Inbox Receiving through Graph','luano@futurasa.co.za',NULL,'NEW',NULL,1,NULL,NULL,NULL,NULL),(3,'AQMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAADxCdhLTQUWk2W-CG7KM1O1AcAbvw1wagjFUmX5m7fswwk9QAAAgEMAAAAbvw1wagjFUmX5m7fswwk9QAAAgVcAAAA','test','nuggets789@gmail.com',NULL,'NEW',NULL,1,NULL,NULL,NULL,NULL),(4,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAIMinMAAA=','Test 5','luano@futurasa.co.za',NULL,'NEW',NULL,1,NULL,NULL,NULL,NULL),(5,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAIhY0BAAA=','Test 7','luano@futurasa.co.za',2,'DEL','2025-12-11 08:30:55.990611',1,'','Email','',NULL),(6,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAIhY0CAAA=','Test 8','luano@futurasa.co.za',NULL,'NEW',NULL,1,NULL,NULL,NULL,NULL),(7,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAIhY0DAAA=','test 9','luano@futurasa.co.za',NULL,'NEW',NULL,1,NULL,NULL,NULL,NULL),(8,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAIhY0EAAA=','Test 10','luano@futurasa.co.za',2,'DEL','2025-12-11 09:14:09.031836',1,'LPI','Email','','2025-12-11 09:13:39.000000'),(9,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAJIxmVAAA=','test 11','luano@futurasa.co.za',NULL,'NEW',NULL,1,NULL,NULL,NULL,'2025-12-12 10:25:09.000000'),(10,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAQfgU-AAA=','Unity_internal','luano@futurasa.co.za',NULL,'NEW',NULL,1,NULL,NULL,NULL,'2025-12-24 06:03:50.000000'),(11,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAQfgU_AAA=','TSRF_recon_app','luano@futurasa.co.za',NULL,'NEW',NULL,1,NULL,NULL,NULL,'2025-12-24 06:03:19.000000'),(12,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAQfgU9AAA=','CRM_unity','luano@futurasa.co.za',NULL,'NEW',NULL,1,NULL,NULL,NULL,'2025-12-24 06:02:30.000000'),(13,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAQfgU8AAA=','ACVV','luano@futurasa.co.za',NULL,'NEW',NULL,1,NULL,NULL,NULL,'2025-12-24 06:01:32.000000'),(14,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAQfgU7AAA=','RE: RE: [MIP: 1510022] New Direct Communication...','testuser@futurasa.co.za',NULL,'NEW',NULL,1,NULL,NULL,NULL,'2025-12-23 09:45:08.000000'),(15,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAQfgU6AAA=','RE: RE: [MIP: 1510022] New Direct Communication...','testuser@futurasa.co.za',NULL,'NEW',NULL,1,NULL,NULL,NULL,'2025-12-23 09:44:33.000000'),(16,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAANp2uBAAA=','[MIP: FAR0396] New Communication','testuser@futurasa.co.za',NULL,'NEW',NULL,1,NULL,NULL,NULL,'2025-12-19 12:20:57.000000'),(17,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAANp2uAAAA=','[MIP: FAR0396] New Communication','testuser@futurasa.co.za',NULL,'NEW',NULL,1,NULL,NULL,NULL,'2025-12-19 12:20:41.000000'),(18,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAMKkydAAA=','RE: [MIP: 1510022] New Direct Communication...','testuser@futurasa.co.za',NULL,'NEW',NULL,1,NULL,NULL,NULL,'2025-12-17 13:15:33.000000'),(19,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAMKkycAAA=','[MIP: 22117] Levy Query','testuser@futurasa.co.za',NULL,'NEW',NULL,1,NULL,NULL,NULL,'2025-12-17 08:52:31.000000'),(20,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAMKkybAAA=','Query: Levy ','testuser@futurasa.co.za',NULL,'NEW',NULL,1,NULL,NULL,NULL,'2025-12-17 08:52:20.000000'),(21,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAMKkyaAAA=','Query: Levy ','testuser@futurasa.co.za',NULL,'NEW',NULL,1,NULL,NULL,NULL,'2025-12-17 08:50:32.000000'),(22,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAMKkyZAAA=','Query: Levy ','testuser@futurasa.co.za',NULL,'NEW',NULL,1,NULL,NULL,NULL,'2025-12-17 08:48:27.000000'),(23,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAMKkyYAAA=','Query: Levy 22117','testuser@futurasa.co.za',NULL,'NEW',NULL,1,NULL,NULL,NULL,'2025-12-17 08:39:53.000000'),(24,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAMKkyXAAA=','Query: Levy 22117','testuser@futurasa.co.za',NULL,'NEW',NULL,1,NULL,NULL,NULL,'2025-12-17 08:38:32.000000'),(25,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAMKkyWAAA=','Query: Levy 22117','testuser@futurasa.co.za',NULL,'NEW',NULL,1,NULL,NULL,NULL,'2025-12-17 08:37:07.000000'),(26,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAMKkyVAAA=','Query: Levy 22117','testuser@futurasa.co.za',NULL,'NEW',NULL,1,NULL,NULL,NULL,'2025-12-17 08:36:24.000000'),(27,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAMKkyUAAA=','Re: Undeliverable: ','testuser@futurasa.co.za',NULL,'NEW',NULL,1,NULL,NULL,NULL,'2025-12-17 06:46:10.000000'),(28,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAJ7P0SAAA=','Undeliverable: ','MAILER-DAEMON@cloud-security.net',NULL,'NEW',NULL,1,NULL,NULL,NULL,'2025-12-15 23:00:18.000000'),(29,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAJ7P0RAAA=','Undeliverable: ','MAILER-DAEMON@cloud-security.net',NULL,'NEW',NULL,1,NULL,NULL,NULL,'2025-12-15 16:00:40.000000'),(30,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAYsUfNAAA=','TEST ATT','luano@futurasa.co.za',NULL,'DLT',NULL,0,'',NULL,'','2026-01-05 06:38:46.000000'),(31,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAYsUfMAAA=','Attachment Test','luano@futurasa.co.za',3,'DEL','2026-01-13 11:30:21.671990',1,'Schedule','Email','PF001','2026-01-04 21:10:56.000000'),(32,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAYsUfLAAA=','Re: test 11','testuser@futurasa.co.za',3,'DEL','2026-01-13 11:43:07.385016',1,'Claim','Email','ACVV Aberdeen (PF001)','2026-01-04 19:34:19.000000');
/*!40000 ALTER TABLE `email_delegation` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `global acvv`
--

DROP TABLE IF EXISTS `global acvv`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `global acvv` (
  `MIP Names` varchar(255) DEFAULT NULL,
  `Branch Code` varchar(255) DEFAULT NULL,
  `MEMBER` varchar(255) DEFAULT NULL,
  `STATUS` varchar(255) DEFAULT NULL,
  `CONTRIBUTION AMOUNT` varchar(255) DEFAULT NULL,
  `NOTES` varchar(255) DEFAULT NULL,
  `SCHEDULE DATE RECEIVED` varchar(255) DEFAULT NULL,
  `DEB ORDER DATE CONFIRM BY EMPOLYER(FUND)` varchar(255) DEFAULT NULL,
  `Bank info Upload` varchar(225) DEFAULT NULL,
  `MG EMAIL ADDRESS` varchar(225) DEFAULT NULL,
  `TEL` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `global acvv`
--

LOCK TABLES `global acvv` WRITE;
/*!40000 ALTER TABLE `global acvv` DISABLE KEYS */;
INSERT INTO `global acvv` VALUES ('MGC001','Alpha Group','Box','Active','PO Box 1234, Cityville','Box','123 Main Street, Cityville','Box','Box','Box','Box'),('ACVV Aberdeen (PF001)','PF001','17','Done','13934,98','21.12.2025','','05.10.2024','Successful','Aalwynhof <aalwynhofacvv@gmail.com>',''),('ACVV Uitenhage ACVV Dienstak (PF002)','PF002','78','Done','70233,17','16.09.2024','100% update member info on RFW','27.09.2024','Successful','Aandmymering Tehuis vir Bejaardes <acvvaandmymering@acvv.org.za>','041 – 9921510'),('ACVV Malmesbury Aandskemering (PF003)','PF003','49','Done','57462,55','25.09.2024','RECEIVED LID INFO upload when SEP is open','27.09.2024','Successful','Personeel <personeel@cornergate.com>','022 482 1466'),('ACVV Piketberg Huis AJ Liebenberg (PF004)','PF004','23','Done','21715,49','04.10.2024','','07.10.2024','Successful','Lana Henrico <payroll@ro.co.za>;manager@hajl.co.za ; Wilma Mouton <Wilma@quattrocitrus.co.za> ;Marelise Vercuiel <marelisevercuiel@gmail.com>',''),('ACVV Algoapark (PF005)','PF005','8','Done','16601,25','27.09.2024','RECEIVED LID INFO upload when SEP is open','01.10.2024','Successful','Colleen Woods <acvvcwoods@gmail.com>',''),('ACVV Williston (PF006)','PF006','11','Done','9286,5','16.09.2024','100% update member info on RFW','25.09.2024','Successful','Amandelhof Kotie Hugo <finans.amandel@hantam.co.za>','053 – 3913 185'),('ACVV Azaleahof ACVV Dienssentrum Dienstak (PF007)','PF007','32','Done','54218,7','04.10.2024','100% update member info on RFW','07.10.2024','Successful','azaleahofacc@adept.co.za',''),('ACVV Olifantshoek Bergen Rus (PF008)','PF008','29','Done','22599,6','25.09.2024','','30.09.2024','','AJ Roelofse <ajroelofse2@gmail.com>',''),('ACVV Riebeek Wes Huis Bergsig (PF009)','PF009','29','Done','31141,53','25.09.2024','100% update member info on RFW','27.09.2024','Partially successful','fin.huisbergsig@acvv.org.za','022-461 2721'),('ACVV Bothasig Creche Dienstak (PF010)','PF010','18','Done','17323,8','25.09.2024','100% update member info on RFW','30.09.2024','Successful','Antoinette Brand <antoinettebrand775@gmail.com>','021-558-4314'),('ACVV Bredasdorp (PF011)','PF011','1','Done','1170,9','27.09.2024','100% update member info on RFW','30.09.2024','Successful','Corrali Groenewald <rekeninge1@suideroord.co.za>','028 424 1080 '),('ACVV Bredasdorp Suidpunt Diens (PF012)','PF012','2','Done','2997,3','27.09.2024','100% update member info on RFW','30.09.2024','Successful','Corrali Groenewald <rekeninge1@suideroord.co.za>','028 424 1080 '),('ACVV Caledon (PF014)','PF014','10','Done','11100,15','23.09.2024','100% update member info on RFW','30.09.2024','Successful','Rocksand Kellerman <fin.acvvdagsorg@gmail.com> ; finans.heidehof@twk.co.za','(023) 316 1505'),('ACVV Ceres (PF018)','PF018','4','Done','9036,75','27.09.2024','100% update member info on RFW','28.09.2024','Successful','fin.ceres@acvv.org.za',''),('ACVV Adelaide (PF019)','PF019','33','Done','21327,96','25.09.2024','100% update member info on RFW','27.09.2024','Successful','Aurelia Loots <aurelialoots@yahoo.com>',''),('ACVV Cradock (PF020)','PF020','9','Done','9978,34','26.09.2024','100% update member info on RFW','04.10.2024','Successful','ACVV Cradock <cradock@acvv.org.za>',''),('ACVV Britstown (PF021)','PF021','14','Done','9160,24','02.10.2024','100% update member info on RFW','07.10.2024','Successful','HUIS DANEEL ADMIN <acvvhuisdaneel@gmail.com>',''),('ACVV Carnarvon Huis Danie van Huyssteen (PF022)','PF022','14','Done','10701,16','30.09.2024','100% update member info on RFW','04.10.2024','Successful','Huis Danie van Huyssteen <huisdanie003805@gmail.com>',''),('ACVV De Aar (PF023)','PF023','4','Done','3300','02.10.2024','100% update member info on RFW','03.10.2024','Successful','ACVV De Aar <fin.acvvdeaar@acvv.org.za>','064 982 8803'),('ACVV De Aar Lollapot (PF023B)','PF023B','8','Done','8033,19','26.09.2024','100% update member info on RFW','27.09.2024','','Elzaan Fourie <elzaan@deaarsa.co.za>',''),('ACVV De Grendel ACVV Dienstak (PF024)','PF024','16','Done','13418,31','27.09.2024','100% update member info on RFW','28.09.2024','Successful','Mandy White <acvvdegrendel@acvv.org.za>',''),('ACVV Delft Dienstak (PF025)','PF025','8','Done','7075,2','16.09.2024','100% update member info on RFW','19.09.2024','Successful','Labelle <acvvlabelle-fin@acvv.org.za>','021 948 2019'),('ACVV Despatch  Dienssentrum (PF026)','PF026','2','Done','1353,28','04.10.2024','100% update member info on RFW','05.10.2024','','ACVV Dienssentrum <dienssentrum2@telkomsa.net>',''),('ACVV Alexandria (PF027)','PF027','32','Done','27603','26.09.2024','','30.09.2024','','ACVV Huis Diaz <fin.huisdiaz@acvv.org.za>',''),('ACVV Tulbagh (PF028)','PF028','18','Done','21065,31','27.09.2024','100% update member info on RFW','04.10.2024','Successful','ACVV Huis Disa <bestuurder.huisdisa@acvv.org.za> ; fin.huisdisa@acvv.org.za',''),('ACVV Dysselsdorp (PF031)','PF031','6','Done','7765,84','01.10.2024','100% update member info on RFW','02.10.2024','','acvvfinansies@scwireless.co.za','044 251 6721 / 062 405 4918'),('ACVV Edelweiss ACVV Dienssentrum en Wooneenhede Dienstak (PF032)','PF032','20','Done','30564','23.09.2024','100% update member info on RFW','26.09.2024','Successful','Edelweiss ACVV <acvvedelweiss@acvv.org.za>','021 9761150'),('ACVV Cradock Elizabeth Jordaan (PF034)','PF034','37','Done','36363,09','27.09.2024','100% update member info on RFW','30.09.2024','Successful','EJT Finansies <fin.ejtehuis@acvv.org.za>','048 8811857'),('ACVV Franschhoek Fleur de Lis (PF035)','PF035','20','Done','20167,2','28.09.2024','100% update member info on RFW','01.10.2024','','fin.acvvfleur@acvv.org.za ; admin@acvvfleur.co.za','021-8762411'),('ACVV Franschhoek (PF036)','PF036','2','Done','4493,08','25.09.2024','100% update member info on RFW','30.09.2024','','sandra@wemz.co.za ; admin@acvvfrans.org.za ; fin@acvvfrans.org.za','021 0231298'),('ACVV Victoria Wes (PF037)','PF037','16','Done','10031,39','28.09.2024','','01.10.2024','Successful','Christina Steenkamp <vicwesacvv2@gmail.com>;Denise Els <elsdenise3@gmail.com>',''),('ACVV Port Elizabeth Wes Huis Genot (PF038)','PF038','41','Done','37080,2','26.09.2024','','30.09.2024','Successful','ACVV Huis Genot <fin.huisgenot@acvv.org.za>',''),('ACVV George (PF039)','PF039','47','Done','65468,57','01.10.2024','100% update member info on RFW','03.10.2024','Successful','Accounts <accountsgrg@acvv.org.za>',''),('ACVV Grabouw (PF040)','PF040','7','Done','16364,56','17.09.2024','100% update member info on RFW','30.09.2024','Successful','fin.huisgroenland@acvv.org.za ; manager@huisgroenland.co.za','021 859 4209'),('ACVV Grabouw Huis Groenland (PF041)','PF041','19','Done','26730','17.09.2024','100% update member info on RFW','30.09.2024','Successful','fin.huisgroenland@acvv.org.za ; manager@huisgroenland.co.za','021 859 4209'),('ACVV Grahamstad (PF042)','PF042','5','Done','4204,74','30.09.2024','100% update member info on RFW','07.10.2024','Successful','ACVV Senior Citizens <fin.grahamstad@acvv.org.za>',''),('ACVV Newton Park PE Haas Das Creche (PF043)','PF043','13','Done','10325,34','01.10.2024','100% update member info on RFW','03.10.2024','Successful','Johannes Petrus Beukman <johanbeukman.irispark@gmail.com>',''),('ACVV Caledon Heidehof (PF044)','PF044','31','Done','38783,25','26.09.2024','100% update member info on RFW','30.09.2024','Successful','finans.heidehof@twk.co.za','028 214 1755'),('ACVV Heidelberg (PF045)','PF045','2','Done','1952,1','27.09.2024','100% update member info on RFW','30.09.2024','Successful','Anne-Marié Keyser <hshfinansies@gmail.com>','028 7221 384'),('ACVV Griekwastad (PF046)','PF046','13','Done','10075,8','23.09.2024','100% update member info on RFW','01.10.2024','Successful','Huis Heldersig <huisheldersig@yahoo.co.za>','053 343 0228'),('ACVV Beaufort-Wes (PF047)','PF047','49','Done','44817','25.09.2024','100% update member info on RFW','27.09.2024','Successful','ACVV Hesperos <acvvhesperos@beaufortwest.net>','023-414-3465'),('ACVV Hoofbestuur (PF048)','PF048','27','Done','118812,92','26.09.2024','100% update member info on RFW','28.09.2024','Successful','andre@acvv.org.za','021-461-7437'),('ACVV Pofadder Huis Sophia (PF049)','PF049','17','Done','14474,45','02.10.2024','','04.10.2024','Successful','Huis Sophia <acvvsophiatehuis@acvv.org.za>','054 933 0297'),('ACVV Strand Huis Jan Swart (PF051)','PF051','20','Done','25294,2','30.09.2024','100% update member info on RFW','02.10.2024','Successful','Boekhouer Huis Jan Swart <accounts@huisjs.co.za>','021 854-3763'),('ACVV Postmasburg Huis Jan Vorster (PF052)','PF052','16','Done','15161,39','04.10.2024','','05.10.2024','','Ronel Dippenaar <roneldip@gmail.com> ; ACVV HuisJanVorster <huisjanvorster@outlook.com>',''),('ACVV Tak Kaapstad (PF053)','PF053','25','','53952,99','','','','Successful','accounts@acvvct.org.za',''),('ACVV Kimberley (PF054)','PF054','3','Done','5008,74','30.09.2024','100% update member info on RFW','01.10.2024','Successful','frans@acvv-kimberley.co.za','053 842 1141'),('ACVV Koeberg (PF056)','PF056','6','Done','13233','25.09.2024','','27.09.2024','Successful','dawnsutton397@gmail.com ; acvvkoeberg@acvv.org.za','021-553-2745'),('ACVV Prins Albert Huis Kweekvallei (PF057)','PF057','23','Done','23175,9','26.09.2024','100% update member info on RFW','04.10.2024','','Munnik <munnik@evolveaa.co.za>','051-410-4200'),('ACVV Kuruman (PF058)','PF058','1','Done','260,4','16.09.2024','100% update member info on RFW','27.09.2024','Successful','ACVV Kuruman <kuruman@acvv.org.za>','0537121862 / 0537121341'),('ACVV La Belle ACVV Dienstak (PF059)','PF059','18','Done','26235,84','16.09.2024','100% update member info on RFW','19.09.2024','Successful','Labelle <acvvlabelle-fin@acvv.org.za>','021 948 2019'),('ACVV L Amour Martinelle Creche (PF060)','PF060','1','Done','1012,5','26.09.2024','100% update member info on RFW','28.09.2024','','Maryna Collins <Lamourm@wo.co.za>',''),('ACVV Magnolia ACVV Dienstak (PF062)','PF062','32','Done','44582,55','19.09.2024','100% update member info on RFW','30.09.2024','Successful','Margherite <money@magnoliaacvv.co.za>','021 - 948 6085'),('ACVV Huis Malan Jacobs ACVV Tehuis vir Bejaardes (PF063)','PF063','21','Done','18040,95','30.09.2024','','01.10.2024','Successful','hmjlaingsburg@gmail.com',''),('ACVV Malmesbury (PF064)','PF064','5','','11658,57','','100% update member info on RFW','','Successful','ACVV Malmesbury Dienssentrum Bestuurder <mbury.dienssentrum@acvv.org.za>',''),('ACVV Somerset Wes Huis Marie Louw (PF065)','PF065','22','Done','24471','27.09.2024','','07.10.2024','Successful','Jo-Ann Theron <fin.huismarielouw@acvv.org.za>',''),('ACVV Ceres Huis Maudie Kriel (PF066)','PF066','51','Done','55755','03.10.2024','RECEIVED LID INFO upload when SEP is open','04.10.2024','Successful','RIANA THEUNISSEN <maudie@lando.co.za>',''),('ACVV Middelburg Oos-Kaap (PF067)','PF067','5','Done','3317,83','25.09.2024','100% update member info on RFW','27.09.2024','Successful','yvonne@adsactive.com',''),('ACVV Kuruman Mimosahof (PF068)','PF068','21','Done','19196,7','25.09.2024','','27.09.2024','Successful','Finansies <mimosahof1@gmail.com>','082-495-5862'),('ACVV Mitchells Plain (PF069)','PF069','10','','19414,6','','','','Successful','accounts@acvvct.org.za',''),('ACVV Montagu (PF070)','PF070','5','Done','8874,49','16.09.2024','100% update member info on RFW','20.09.2024','Successful','ACVV Montagu <admin@acvvmontagu.co.za>','023-614-1490'),('ACVV Moorreesburg (PF071)','PF071','35','Done','35463,53','27.09.2024','100% update member info on RFW','07.10.2024','Successful','Huismoorrees Fin <huismoorreesfin@pcnetmail.co.za>','022-433-1477'),('ACVV Moreson ACVV Kinder- en Jeugsorgsentrum (PF072)','PF072','27','Done','47295,15','26.09.2024','','30.09.2024','Successful','Môreson Treasurer <moreson.admin@acvv.org.za>','044 874 4798'),('ACVV Mosselbaai (PF073)','PF073','123','Done','136371,15','26.09.2024','','30.09.2024','','Jan Venter <mosselbaaitesourier@acvv.org.za>',''),('ACVV Springbok Huis Namakwaland (PF074)','PF074','32','Done','26888,25','25.09.2024','100% update member info on RFW','30.09.2024','Successful','FINANSIES <finance@huisnamakwaland.co.za> ; andre@acvv.org.za',''),('ACVV Despatch Huis Najaar (PF075)','PF075','14','Done','11893,2','26.09.2024','','03.10.2024','Successful','accounts@huisnajaar.co.za',''),('ACVV Porterville Tak Huis Nerina (PF076)','PF076','32','Done','34259,61','16.09.2024','100% update member info on RFW','18.09.2024','Successful','Sunette Beck <fin.huisnerina@acvv.org.za>','022 931 2720'),('ACVV Dordrecht (PF077)','PF077','16','Done','12145,1','26.09.2024','100% update member info on RFW','07.10.2024','','Nerinahof Ouetehuis <nerinahof@gmail.com>',''),('ACVV Worcester (PF078)','PF078','50','Done','56611,91','01.10.2024','','03.10.2024','','finansies@nuwerus.co.za',''),('ACVV Paarl Vallei Oase Dienssentrum (PF079)','PF079','3','Done','3066,54','26.09.2024','100% update member info on RFW','30.09.2024','Successful','Finansies | ACVV Paarl Vallei  <info@acvv-pvallei.org.za>','021-871-1515'),('ACVV Kimberley Ons Huis (PF080)','PF080','25','Done','21343,88','30.09.2024','100% update member info on RFW','01.10.2024','Successful','frans@acvv-kimberley.co.za','053 842 1141'),('ACVV Ons Tuiste ACVV Dienstak (PF081)','PF081','53','Done','73418,85','27.09.2024','100% update member info on RFW','28.09.2024','Successful','Lizandra - Ons Tuiste <fin.ons-tuiste@acvv.org.za>',''),('ACVV Op die Kruin ACVV Dienstak (PF082)','PF082','9','Done','5228,4','19.09.2024','100% update member info on RFW','27.09.2024','Successful','OpDieKruin ACVV <acvvopdiekruin@gmail.com> ; Gerhard Engelbrecht <mrg8181@gmail.com>','053 631 3130'),('ACVV Upington Oranjehof Tehuis (PF083)','PF083','31','Done','41999,1','02.10.2024','100% update member info on RFW','04.10.2024','','Admin Oranjehof ACVV Tehuis vir Bejaardes <admin@acvvoranjehof.co.za>','054 331 2044 / 054 332 1986'),('ACVV Caledon (PF014)','PF014','10','Done','11100,15','23.09.2024','100% update member info on RFW','30.09.2024','Successful','Rocksand Kellerman <fin.acvvdagsorg@gmail.com> ; finans.heidehof@twk.co.za','(023) 316 1505'),('ACVV Oudtshoorn (PF085)','PF085','147','Done','145608,8','26.09.2024','RECEIVED LID INFO upload when SEP is open','27.09.2024','Successful','Finansies @ Odn ACVV <fin.oudtshoorn@acvv.org.za>','044-272-2211'),('ACVV Paarl (PF086)','PF086','3','Done','6744,9','23.09.2024','100% update member info on RFW','25.09.2024','Successful','ACVV Paarl Tak <acvvpaarl@gmail.com>','021 872-2738'),('ACVV Noorder-Paal (PF087)','PF087','3','Done','8632,98','23.09.2024','100% update member info on RFW','27.09.2024','Successful','admin@acvvnp.org.za',''),('ACVV Paarl Vallei (PF088)','PF088','5','Done','9879,81','26.09.2024','100% update member info on RFW','30.09.2024','Successful','Finansies | ACVV Paarl Vallei  <info@acvv-pvallei.org.za>','021-871-1515'),('ACVV Newton Park PE (PF089)','PF089','2','Done','4308,78','01.10.2024','100% update member info on RFW','03.10.2024','Successful','From','Subject'),('ACVV PE Noord (PF090)','PF090','4','Done','7381,52','01.10.2024','100% update member info on RFW','','Successful','Johannes Petrus Beukman','Fwd: Pension Fund Sep 2024'),('ACVV Port Elizabeth Suid (PF092)','PF092','6','Done','7206,36','03.10.2024','100% update member info on RFW','05.10.2024','Successful','ADMIN - ACVV POPLARLAAN <admin@poplarlaan.acvv.co.za> ; Mary-Ann Coetzer <book@pesuid.acvv.co.za>',''),('ACVV Port Elizabeth Wes (PF093)','PF093','11','Done','23725,85','16.09.2024','100% update member info on RFW','23.09.2024','Successful','Accounts <accounts.pewes@lantic.net>','041 360 2106'),('ACVV Piketberg (PF094)','PF094','4','Done','9074,78','23.09.2024','100% update member info on RFW','30.09.2024','Successful','Elmarie van Rooyen <fin.piketberg@acvv.org.za>',''),('ACVV St Helenabaai (PF095)','PF095','16','Done','17151,19','25.09.2024','100% update member info on RFW','26.09.2024','Successful','aletta@visagieboerdery.com',''),('ACVV Poplarlaan PE (PF096)','PF096','2','Done','2400,68','01.10.2024','100% update member info on RFW','07.10.2024','Successful','ADMIN - ACVV POPLARLAAN <admin@poplarlaan.acvv.co.za>','060 810 6260 '),('ACVV Porterville Tak (PF097)','PF097','2','Done','3916,16','20.09.2024','100% update member info on RFW','25.09.2024','Successful','Sunette Beck <fin.huisnerina@acvv.org.za>','022 931 2720'),('ACVV Postmasburg (PF098)','PF098','1','Done','1271,38','25.09.2024','100% update member info on RFW','30.09.2024','Successful','ACVV Postmasburg <pmgacvv@gmail.com>','053 313 2164'),('ACVV Prieska (PF099)','PF099','4','','5480,11','','100% update member info on RFW','','','fin.prieska@acvv.org.za',''),('ACVV Caledon Protea Dienssentrum (PF100)','PF100','1','Done','672,58','26.09.2024','100% update member info on RFW','30.09.2024','Successful','finans.heidehof@twk.co.za','028 214 1755'),('ACVV Riebeek Kasteel (PF101)','PF101','9','Done','17476,06','16.09.2024','100% update member info on RFW','27.09.2024','Successful','ACVV Riebeek Kasteel Manager <manager@acvvrk.org>','(022) 448-1715'),('ACVV Riversdal (PF102)','PF102','11','Done','17832,41','25.09.2024','100% update member info on RFW','30.09.2024','Successful','info@shovelprojects.co.za','028-713-1378'),('ACVV Robertson Huis Le Roux (PF103)','PF103','22','Done','25557,56','23.09.2024','100% update member info on RFW','27.09.2024','Successful','ACVV Huis le Roux <fin.huisleroux@acvv.org.za>','(023) 626-3163'),('ACVV Robertson (PF104)','PF104','10','Done','13308,6','16.09.2024','100% update member info on RFW','23.09.2024','Successful','fin2 <fin2@acvvrobertson.org.za>','023-626-3097'),('ACVV Rusoord Tehuis vir Oues van Dae Paarl (PF105)','PF105','35','Done','44169,65','26.09.2024','100% update member info on RFW','04.10.2024','Successful','finansies@rusoordtehuis.co.za ; Lucinda Scholtz <bestuurder@rusoordtehuis.co.za>',''),('ACVV Clanwilliam (PF106)','PF106','28','Done','29596,8','26.09.2024','RECEIVED LID INFO upload when SEP is open','04.10.2024','Successful','Admin <admin@acvvsederhof.org.za>',''),('ACVV Somerset Oos Huis Silwerjare (PF107)','PF107','12','Done','8554,92','27.09.2024','100% update member info on RFW','04.10.2024','Successful','Rika Scheun <fin.silwerjare@acvv.org.za>','04224 32107'),('ACVV Wellington Tak Silwerkruin (PF108)','PF108','62','Done','66027,42','19.09.2024','100% update member info on RFW','23.09.2024','','Johanitia Coetzee <finans1@silwerkruin.com>','021-873-1040'),('ACVV Elizabeth Roos Tehuis Dienstak (PF110)','PF110','11','Done','14805,3','25.09.2024','100% update member info on RFW','30.09.2024','Successful','Accounts Elizabeth Roos <bookkeeper.elizabethroos@gmail.com>','021-462-1638'),('ACVV Skiereiland Beheerkomitee van die ACVV Dienstak (PF111)','PF111','12','Done','28050,84','25.09.2024','100% update member info on RFW','27.09.2024','','Albida McMillan <accounts@acvvpen.co.za>',''),('ACVV Strand Soeterus Tehuis (PF112)','PF112','23','Done','23812,5','25.09.2024','100% update member info on RFW','27.09.2024','Successful','Amanda Klem <finansies@soeterus.com>','(021) 853 7423'),('ACVV Lambersbaai Somerkoelte Tehuis (PF113)','PF113','37','','31030,71','','100% update member info on RFW','','Successful','somerkoelte.finansies@gmail.com',''),('ACVV Somerset Wes (PF115)','PF115','5','Done','12861,2','20.09.2024','100% update member info on RFW','30.09.2024','Successful','ACVV SWES <acvvswes@telkomsa.net>','021-852-2103'),('ACVV De Aar Sonder Sorge Tehuis (PF117)','PF117','25','Done','21839,81','23.09.2004','100% update member info on RFW','06.10.2024','Successful','Riana Raath <truteriana@gmail.com>',''),('ACVV Calvinia (PF118)','PF118','35','Done','32498,85','20.09.2024','RECEIVED LID INFO upload when SEP is open','28.09.2024','Successful','Sorgvliet Tehuis <sorgvliet@hantam.co.za>','027-341-1223'),('ACVV Strand Speelkasteel (PF120)','PF120','17','Done','19876,5','01.10.2024','100% update member info on RFW','03.10.2024','Successful','Speelkasteel Strand boekhouer <speelkasteelstrandboekhouer@acvv.org.za> ; speelkasteelstrand@acvv.org.za',''),('ACVV Douglas (PF121)','PF121','31','Done','34599,7','23.09.2024','100% update member info on RFW','27.09.2024','Successful','ACVV Spes Bona <fin.spesbona@acvv.org.za>','053 298 1035'),('ACVV Stellenbosch (PF123)','PF123','20','Done','33941,18','25.09.2024','100% update member info on RFW','30.09.2024','Successful','fin.stellenbosch@acvv.org.za','021 887 6959'),('ACVV Worcester Stilwaters Dienssentrum (PF124)','PF124','3','Done','3894','27.09.2024','100% update member info on RFW','28.09.2024','Successful','Brian Baard <stilwatersfin@acvvcw.co.za>','(023) 342 0634'),('ACVV Die Afrikaanse Christelike Vrouevereniging Strand (PF125)','PF125','12','Done','25858,65','30.09.2024','100% update member info on RFW','04.10.2024','Successful','Jacqueline Dippenaar <strandadmin@acvv.org.za>','(021) 854 7215'),('ACVV Bredasdorp Suideroord Tehuis (PF126)','PF126','92','Done','111220,95','27.09.2024','RECEIVED LID INFO upload when SEP is open','30.09.2024','Successful','Corrali Groenewald <rekeninge1@suideroord.co.za>','028 424 1080 '),('ACVV Swellendam (PF127)','PF127','3','Done','6849,75','16.09.2024','100% update member info on RFW','25.09.2024','Successful','Ronel Groenewald <fin.swellendam@acvv.org.za>',''),('ACVV Middelburg Oos Kaap Huis Karee (PF130)','PF130','10','Done','12134,77','25.09.2024','100% update member info on RFW','30.09.2024','Successful','huiskaree@gmail.com','049-842-2151'),('ACVV Upington (PF131)','PF131','6','','10059,64','','100% update member info on RFW','','','acvv@isat.co.za',''),('ACVV Utopia ACVV Tehuis vir Bejaardes Dienstak (PF132)','PF132','10','Done','20385,96','16.09.2024','100% update member info on RFW','27.09.2024','Successful','anneen@utopiastb.co.za , Annelie van Eeden <annelie@ffas.co.za> , admin@utopiastb.co.za , Lila Botha <lilabotha1602@gmail.com>',''),('ACVV Kirkwood Valleihof Tehuis (PF133)','PF133','28','Done','28634,1','25.09.2024','100% update member info on RFW','26.09.2024',' ','fin.valleihof@acvv.org.za','042 2300 393'),('ACVV Graaff-Reinet Huis van de Graaff Tehuis (PF134)','PF134','25','Done','18160,94','25.09.2024','','04.10.2024','','ACVV Graaff-Reinet <acvvgraaffreinet@telkomsa.net>','049-892-3229'),('ACVV Huis Van Niekerk Benadehof ACVV Dienssentrum Dienstak (PF135)','PF135','45','Done','78080,85','23.09.2024','','26.09.2024','Successful','Charmaine van den Heuvel <finansies@vnbh.org.za>','021 853 1040/1'),('ACVV Huis Vergenoegd Dienstak Diens en Dag (Paarl) (PF136)','PF136','3','Done','13568,99','01.10.2024','100% update member info on RFW','03.10.2024','Successful','Morné Swanepoel <hvg1@lando.co.za>',''),('ACVV Huis Vergenoegd Dienstak Siekeboeg (Paarl) (PF137)','PF137','72','Done','100099,47','01.10.2024','RECEIVED LID INFO upload when SEP is open','02.10.2024','Successful','Morné Swanepoel <hvg1@lando.co.za>',''),('ACVV Huis Vergenoegd Dienstak Woonstelle (Paarl) (PF138)','PF138','33','Done','42133,42','01.10.2024','','03.10.2024','Successful','Morné Swanepoel <hvg1@lando.co.za>',''),('ACVV Wellington Tak (PF139)','PF139','2','Done','5424','17.09.2024','100% update member info on RFW','05.10.2024','Successful','Steven von Schlicht <well.admin@acvv.org.za>','021-873-2204'),('ACVV Wellington Tak Fyngoud Dienssentrum (PF140)','PF140','2','Done','3660,66','04.10.2024','100% update member info on RFW','05.10.2024','Successful','Adri van Zyl <acvvfyngoud@acvv.org.za>',''),('ACVV Paarl Vallei Wielie Walie Creche (PF141)','PF141','6','Done','5558,86','26.09.2024','100% update member info on RFW','30.09.2024','Successful','Finansies | ACVV Paarl Vallei  <info@acvv-pvallei.org.za>','021-871-1515'),('ACVV Weskusnessie Dienstak (PF142)','PF142','23','Done','23393,5','03.10.2024','100% update member info on RFW','04.10.2024','Successful','Lizl Ryan <lizlryan@gmail.com>',''),('ACVV Danielskuil (PF143)','PF143','5','Done','6700,11','30.09.2024','100% update member info on RFW','04.10.2024','Successful','acvvdanielskuil <acvvdanielskuil@gmail.com>',''),('ACVV Victoria Wes Wiekie Wessie Creche (PF144)','PF144','1','Done','712,39','28.09.2024','','01.10.2024','','Christina Steenkamp <vicwesacvv2@gmail.com>;Denise Els <elsdenise3@gmail.com>',''),('ACVV Worcester (PF145)','PF145','4','Done','7765,8','27.09.2024','100% update member info on RFW','28.09.2024','Successful','Brian Baard <stilwatersfin@acvvcw.co.za>','(023) 342 0634'),('ACVV Ysterplaat Dienstak van die ACVV (PF146)','PF146','29','Done','31781,75','25.09.2024','100% update member info on RFW','27.09.2024','Successful','Finance Ria Abel Home <finances@homeriaabel.co.za>','021-511-8119'),('ACVV Zonnebloem ACVV Dienstak (PF147)','PF147','41','Done','39234,15','30.09.2024','RECEIVED LID INFO upload when SEP is open','01.10.2024','Successful','Moira Marincowitz <zonnebloemfinansies@acvv.org.za>',''),('ACVV Strand Dienssentrum vir Seniors (PF148)','PF148','4','Done','12411,62','27.09.2024','100% update member info on RFW','01.10.2024','Successful','Domé Sonnekus <admin@strandsds.co.za> ; info@strandsds.co.za',''),('ACVV Grabouw Appelkontrei Dienssentrum (PF149)','PF149','1','Done','1518','17.09.2024','100% update member info on RFW','30.09.2024','Successful','fin.huisgroenland@acvv.org.za ; manager@huisgroenland.co.za','021 859 4209'),('ACVV Reivilo Dienssentrum (PF150)','PF150','4','Done','1200','27.09.2024','100% update member info on RFW','01.10.2024','','Leone Jansen van vuuren <leone.jansenvanvuuren@gmail.com> ; doretteweideman@gmail.com',''),('ACVV Elandsbaai (PF151)','PF151','2','Done','2491,6','20.09.2024','100% update member info on RFW','25.09.2024','Successful','Marlise Smit <marlise@smitrek.co.za>','060-995-7365'),('ACVV Colesberg Old Age Home (PF155)','PF155','7','Done','6672,32','23.09.2024','100% update member info on RFW','27.09.2024','Successful','Huis Kiepersol Huis Kiepersol <huiskiepersol1@gmail.com>',''),('ACVV Triomf Child Care Centre (PF156)','PF156','8','Done','8321','26.09.2024','100% update member info on RFW','07.10.2024','Successful','Sharon Hay <sharon@thebarn.co.za>',''),('ACVV Barrydale (PF157)','PF157','1','Done','1170,9','25.09.2024','100% update member info on RFW','27.09.2024','Successful','Lucinda Van der Berg <fin.barrydale@acvv.org.za>','028 572 1995 | Cell: 0711279004'),('ACVV Malmesbury Dienssentrum (PF161)','PF161','4','','4771,86','','100% update member info on RFW','','Successful','malmesbury.tak@acvv.org.za',''),('ACVV Somerset Wes Tinktinkie (PF163)','PF163','5','Done','4596,38','20.09.2024','100% update member info on RFW','30.09.2024','Successful','ACVV SWES <acvvswes@telkomsa.net>','021-852-2103'),('ACVV Despatch (PF165)','PF165','2','Done','2969,96','04.10.2024','100% update member info on RFW','07.10.2024','Successful','Wilma Laubscher <socialworker@acvvdespatch.co.za>',''),('ACVV Kuruman Heuwelsig (PF166)','PF166','4','Done','5123,94','20.09.2024','100% update member info on RFW','25.09.2024','Successful','fin.heuwelsig <fin.heuwelsig@acvv.org.za>','053-712-0447'),('ACVV Port Elizabeth Sentraal Khayalethu Jeugsentrum (PF168)','PF168','11','Done','21507,75','20.09.2024','100% update member info on RFW','30.09.2024','Successful','Amelia Otto <bookkeeper@khayalethu.org.za> ; Marietjie <khaya@khayalethu.org.za>','041 484 5667'),('ACVV Piketberg Trippe Trappe (PF169)','PF169','5','Done','4585,66','23.09.2024','100% update member info on RFW','30.09.2024','Successful','Elmarie van Rooyen <fin.piketberg@acvv.org.za>',''),('ACVV Robertson Jakaranda Dienssentrum (PF171)','PF171','3','Done','4008','16.09.2024','100% update member info on RFW','23.09.2024','','fin2 <fin2@acvvrobertson.org.za>','023-626-3097'),('ACVV Worcester Bollieland Creche (PF172)','PF172','11','Done','10606,12','02.10.2024','100% update member info on RFW','03.10.2024','Successful','ACVV Bollieland Creche <fin.bollieland@acvv.org.za>','023-342-0760'),('ACVV Moorreesburg Kleuterland (PF173)','PF173','10','Done','10142,89','27.09.2024','100% update member info on RFW','07.10.2024','Successful','Huismoorrees Fin <huismoorreesfin@pcnetmail.co.za>','022-433-1477'),('ACVV Moorreesburg (PF174)','PF174','5','Done','8936,7','27.09.2024','100% update member info on RFW','07.10.2024','Successful','Huismoorrees Fin <huismoorreesfin@pcnetmail.co.za>','022-433-1477'),('ACVV Dienssentrum Moorreesburg (PF175)','PF175','2','Done','2007,21','27.09.2024','100% update member info on RFW','07.10.2024','Successful','Huismoorrees Fin <huismoorreesfin@pcnetmail.co.za>','022-433-1477'),('ACVV Moorreesburg Heuwelsig (PF176)','PF176','1','Done','784,89','27.09.2004','100% update member info on RFW','07.10.2024','Successful','Huismoorrees Fin <huismoorreesfin@pcnetmail.co.za>','022-433-1477'),('ACVV Dysselsdorp Swartberg Dienssentrum (PF181)','PF181','2','Done','1296,08','30.09.2024','100% update member info on RFW','02.10.2024','','acvvfinansies@scwireless.co.za','044 251 6721 / 062 405 4918'),('ACVV Dysselsdorp Siembamba Creche (PF182)','PF182','5','Done','2880','30.09.2024','100% update member info on RFW','02.10.2024','','acvvfinansies@scwireless.co.za','044 251 6721 / 062 405 4918'),('ACVV Yzerfontein','PF183','1','Done','1525,71','20.09.2024','100% update member info on RFW','25.09.2024','','acvvyzerfontein@gmail.com','022 451 2494'),('ACVV Dysselsdorp Shelter (PF184)','PF184','3','Done','2360,12','30.09.2024','100% update member info on RFW','02.10.2024','','acvvfinansies@scwireless.co.za','044 251 6721 / 062 405 4918'),('ACVV Riebeek Wes Humanitas (PF050)= PF185 ','PF185','2','Done','1358,6','02.10.2024','100% update member info on RFW','03.10.2024','Successful','fin.riebeekwes@acvv.org.za','022-461 2721'),('ACVV Port Elizabeth Sentraal (PF091)PF186)','PF186','1','Done','1845','03.10.2024','100% update member info on RFW','05.10.2024','Successful','elko@iafrica.com',''),('ACVV Marinerylaan (PF180)','PF180','1','NEW FUND 01.08.2024','','','nuwe lid vanaf 1.08.2024 wag op christel -tak ni aktief op rfw nie','','','johanbeukman.irispark@gmail.com','');
/*!40000 ALTER TABLE `global acvv` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `reconciliation_record`
--

DROP TABLE IF EXISTS `reconciliation_record`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `reconciliation_record` (
  `id` int NOT NULL AUTO_INCREMENT,
  `fiscal_month` date NOT NULL,
  `mip_name` varchar(255) NOT NULL,
  `branch_code` varchar(50) NOT NULL,
  `billed_amount` decimal(12,2) DEFAULT '0.00',
  `paid_amount` decimal(12,2) DEFAULT '0.00',
  `outstanding_amount` decimal(12,2) DEFAULT '0.00',
  `note` text,
  `is_closed` tinyint(1) DEFAULT '0',
  `closed_at` datetime(6) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_fiscal_mip` (`fiscal_month`,`mip_name`)
) ENGINE=InnoDB AUTO_INCREMENT=157 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `reconciliation_record`
--

LOCK TABLES `reconciliation_record` WRITE;
/*!40000 ALTER TABLE `reconciliation_record` DISABLE KEYS */;
INSERT INTO `reconciliation_record` VALUES (1,'2026-01-08','MGC001','Alpha Group',0.00,0.00,0.00,NULL,0,NULL),(2,'2026-01-08','ACVV Aberdeen (PF001)','PF001',0.00,0.00,0.00,NULL,0,NULL),(3,'2026-01-08','ACVV Uitenhage ACVV Dienstak (PF002)','PF002',0.00,0.00,0.00,NULL,0,NULL),(4,'2026-01-08','ACVV Malmesbury Aandskemering (PF003)','PF003',0.00,0.00,0.00,NULL,0,NULL),(5,'2026-01-08','ACVV Piketberg Huis AJ Liebenberg (PF004)','PF004',0.00,0.00,0.00,NULL,0,NULL),(6,'2026-01-08','ACVV Algoapark (PF005)','PF005',0.00,0.00,0.00,NULL,0,NULL),(7,'2026-01-08','ACVV Williston (PF006)','PF006',0.00,0.00,0.00,NULL,0,NULL),(8,'2026-01-08','ACVV Azaleahof ACVV Dienssentrum Dienstak (PF007)','PF007',0.00,0.00,0.00,NULL,0,NULL),(9,'2026-01-08','ACVV Olifantshoek Bergen Rus (PF008)','PF008',0.00,0.00,0.00,NULL,0,NULL),(10,'2026-01-08','ACVV Riebeek Wes Huis Bergsig (PF009)','PF009',0.00,0.00,0.00,NULL,0,NULL),(11,'2026-01-08','ACVV Bothasig Creche Dienstak (PF010)','PF010',0.00,0.00,0.00,NULL,0,NULL),(12,'2026-01-08','ACVV Bredasdorp (PF011)','PF011',0.00,0.00,0.00,NULL,0,NULL),(13,'2026-01-08','ACVV Bredasdorp Suidpunt Diens (PF012)','PF012',0.00,0.00,0.00,NULL,0,NULL),(14,'2026-01-08','ACVV Caledon (PF014)','PF014',0.00,0.00,0.00,NULL,0,NULL),(15,'2026-01-08','ACVV Ceres (PF018)','PF018',0.00,0.00,0.00,NULL,0,NULL),(16,'2026-01-08','ACVV Adelaide (PF019)','PF019',0.00,0.00,0.00,NULL,0,NULL),(17,'2026-01-08','ACVV Cradock (PF020)','PF020',0.00,0.00,0.00,NULL,0,NULL),(18,'2026-01-08','ACVV Britstown (PF021)','PF021',0.00,0.00,0.00,NULL,0,NULL),(19,'2026-01-08','ACVV Carnarvon Huis Danie van Huyssteen (PF022)','PF022',0.00,0.00,0.00,NULL,0,NULL),(20,'2026-01-08','ACVV De Aar (PF023)','PF023',0.00,0.00,0.00,NULL,0,NULL),(21,'2026-01-08','ACVV De Aar Lollapot (PF023B)','PF023B',0.00,0.00,0.00,NULL,0,NULL),(22,'2026-01-08','ACVV De Grendel ACVV Dienstak (PF024)','PF024',0.00,0.00,0.00,NULL,0,NULL),(23,'2026-01-08','ACVV Delft Dienstak (PF025)','PF025',0.00,0.00,0.00,NULL,0,NULL),(24,'2026-01-08','ACVV Despatch  Dienssentrum (PF026)','PF026',0.00,0.00,0.00,NULL,0,NULL),(25,'2026-01-08','ACVV Alexandria (PF027)','PF027',0.00,0.00,0.00,NULL,0,NULL),(26,'2026-01-08','ACVV Tulbagh (PF028)','PF028',0.00,0.00,0.00,NULL,0,NULL),(27,'2026-01-08','ACVV Dysselsdorp (PF031)','PF031',0.00,0.00,0.00,NULL,0,NULL),(28,'2026-01-08','ACVV Edelweiss ACVV Dienssentrum en Wooneenhede Dienstak (PF032)','PF032',0.00,0.00,0.00,NULL,0,NULL),(29,'2026-01-08','ACVV Cradock Elizabeth Jordaan (PF034)','PF034',0.00,0.00,0.00,NULL,0,NULL),(30,'2026-01-08','ACVV Franschhoek Fleur de Lis (PF035)','PF035',0.00,0.00,0.00,NULL,0,NULL),(31,'2026-01-08','ACVV Franschhoek (PF036)','PF036',0.00,0.00,0.00,NULL,0,NULL),(32,'2026-01-08','ACVV Victoria Wes (PF037)','PF037',0.00,0.00,0.00,NULL,0,NULL),(33,'2026-01-08','ACVV Port Elizabeth Wes Huis Genot (PF038)','PF038',0.00,0.00,0.00,NULL,0,NULL),(34,'2026-01-08','ACVV George (PF039)','PF039',0.00,0.00,0.00,NULL,0,NULL),(35,'2026-01-08','ACVV Grabouw (PF040)','PF040',0.00,0.00,0.00,NULL,0,NULL),(36,'2026-01-08','ACVV Grabouw Huis Groenland (PF041)','PF041',0.00,0.00,0.00,NULL,0,NULL),(37,'2026-01-08','ACVV Grahamstad (PF042)','PF042',0.00,0.00,0.00,NULL,0,NULL),(38,'2026-01-08','ACVV Newton Park PE Haas Das Creche (PF043)','PF043',0.00,0.00,0.00,NULL,0,NULL),(39,'2026-01-08','ACVV Caledon Heidehof (PF044)','PF044',0.00,0.00,0.00,NULL,0,NULL),(40,'2026-01-08','ACVV Heidelberg (PF045)','PF045',0.00,0.00,0.00,NULL,0,NULL),(41,'2026-01-08','ACVV Griekwastad (PF046)','PF046',0.00,0.00,0.00,NULL,0,NULL),(42,'2026-01-08','ACVV Beaufort-Wes (PF047)','PF047',0.00,0.00,0.00,NULL,0,NULL),(43,'2026-01-08','ACVV Hoofbestuur (PF048)','PF048',0.00,0.00,0.00,NULL,0,NULL),(44,'2026-01-08','ACVV Pofadder Huis Sophia (PF049)','PF049',0.00,0.00,0.00,NULL,0,NULL),(45,'2026-01-08','ACVV Strand Huis Jan Swart (PF051)','PF051',0.00,0.00,0.00,NULL,0,NULL),(46,'2026-01-08','ACVV Postmasburg Huis Jan Vorster (PF052)','PF052',0.00,0.00,0.00,NULL,0,NULL),(47,'2026-01-08','ACVV Tak Kaapstad (PF053)','PF053',0.00,0.00,0.00,NULL,0,NULL),(48,'2026-01-08','ACVV Kimberley (PF054)','PF054',0.00,0.00,0.00,NULL,0,NULL),(49,'2026-01-08','ACVV Koeberg (PF056)','PF056',0.00,0.00,0.00,NULL,0,NULL),(50,'2026-01-08','ACVV Prins Albert Huis Kweekvallei (PF057)','PF057',0.00,0.00,0.00,NULL,0,NULL),(51,'2026-01-08','ACVV Kuruman (PF058)','PF058',0.00,0.00,0.00,NULL,0,NULL),(52,'2026-01-08','ACVV La Belle ACVV Dienstak (PF059)','PF059',0.00,0.00,0.00,NULL,0,NULL),(53,'2026-01-08','ACVV L Amour Martinelle Creche (PF060)','PF060',0.00,0.00,0.00,NULL,0,NULL),(54,'2026-01-08','ACVV Magnolia ACVV Dienstak (PF062)','PF062',0.00,0.00,0.00,NULL,0,NULL),(55,'2026-01-08','ACVV Huis Malan Jacobs ACVV Tehuis vir Bejaardes (PF063)','PF063',0.00,0.00,0.00,NULL,0,NULL),(56,'2026-01-08','ACVV Malmesbury (PF064)','PF064',0.00,0.00,0.00,NULL,0,NULL),(57,'2026-01-08','ACVV Somerset Wes Huis Marie Louw (PF065)','PF065',0.00,0.00,0.00,NULL,0,NULL),(58,'2026-01-08','ACVV Ceres Huis Maudie Kriel (PF066)','PF066',0.00,0.00,0.00,NULL,0,NULL),(59,'2026-01-08','ACVV Middelburg Oos-Kaap (PF067)','PF067',0.00,0.00,0.00,NULL,0,NULL),(60,'2026-01-08','ACVV Kuruman Mimosahof (PF068)','PF068',0.00,0.00,0.00,NULL,0,NULL),(61,'2026-01-08','ACVV Mitchells Plain (PF069)','PF069',0.00,0.00,0.00,NULL,0,NULL),(62,'2026-01-08','ACVV Montagu (PF070)','PF070',0.00,0.00,0.00,NULL,0,NULL),(63,'2026-01-08','ACVV Moorreesburg (PF071)','PF071',0.00,0.00,0.00,NULL,0,NULL),(64,'2026-01-08','ACVV Moreson ACVV Kinder- en Jeugsorgsentrum (PF072)','PF072',0.00,0.00,0.00,NULL,0,NULL),(65,'2026-01-08','ACVV Mosselbaai (PF073)','PF073',0.00,0.00,0.00,NULL,0,NULL),(66,'2026-01-08','ACVV Springbok Huis Namakwaland (PF074)','PF074',0.00,0.00,0.00,NULL,0,NULL),(67,'2026-01-08','ACVV Despatch Huis Najaar (PF075)','PF075',0.00,0.00,0.00,NULL,0,NULL),(68,'2026-01-08','ACVV Porterville Tak Huis Nerina (PF076)','PF076',0.00,0.00,0.00,NULL,0,NULL),(69,'2026-01-08','ACVV Dordrecht (PF077)','PF077',0.00,0.00,0.00,NULL,0,NULL),(70,'2026-01-08','ACVV Worcester (PF078)','PF078',0.00,0.00,0.00,NULL,0,NULL),(71,'2026-01-08','ACVV Paarl Vallei Oase Dienssentrum (PF079)','PF079',0.00,0.00,0.00,NULL,0,NULL),(72,'2026-01-08','ACVV Kimberley Ons Huis (PF080)','PF080',0.00,0.00,0.00,NULL,0,NULL),(73,'2026-01-08','ACVV Ons Tuiste ACVV Dienstak (PF081)','PF081',0.00,0.00,0.00,NULL,0,NULL),(74,'2026-01-08','ACVV Op die Kruin ACVV Dienstak (PF082)','PF082',0.00,0.00,0.00,NULL,0,NULL),(75,'2026-01-08','ACVV Upington Oranjehof Tehuis (PF083)','PF083',0.00,0.00,0.00,NULL,0,NULL),(76,'2026-01-08','ACVV Oudtshoorn (PF085)','PF085',0.00,0.00,0.00,NULL,0,NULL),(77,'2026-01-08','ACVV Paarl (PF086)','PF086',0.00,0.00,0.00,NULL,0,NULL),(78,'2026-01-08','ACVV Noorder-Paal (PF087)','PF087',0.00,0.00,0.00,NULL,0,NULL),(79,'2026-01-08','ACVV Paarl Vallei (PF088)','PF088',0.00,0.00,0.00,NULL,0,NULL),(80,'2026-01-08','ACVV Newton Park PE (PF089)','PF089',0.00,0.00,0.00,NULL,0,NULL),(81,'2026-01-08','ACVV PE Noord (PF090)','PF090',0.00,0.00,0.00,NULL,0,NULL),(82,'2026-01-08','ACVV Port Elizabeth Suid (PF092)','PF092',0.00,0.00,0.00,NULL,0,NULL),(83,'2026-01-08','ACVV Port Elizabeth Wes (PF093)','PF093',0.00,0.00,0.00,NULL,0,NULL),(84,'2026-01-08','ACVV Piketberg (PF094)','PF094',0.00,0.00,0.00,NULL,0,NULL),(85,'2026-01-08','ACVV St Helenabaai (PF095)','PF095',0.00,0.00,0.00,NULL,0,NULL),(86,'2026-01-08','ACVV Poplarlaan PE (PF096)','PF096',0.00,0.00,0.00,NULL,0,NULL),(87,'2026-01-08','ACVV Porterville Tak (PF097)','PF097',0.00,0.00,0.00,NULL,0,NULL),(88,'2026-01-08','ACVV Postmasburg (PF098)','PF098',0.00,0.00,0.00,NULL,0,NULL),(89,'2026-01-08','ACVV Prieska (PF099)','PF099',0.00,0.00,0.00,NULL,0,NULL),(90,'2026-01-08','ACVV Caledon Protea Dienssentrum (PF100)','PF100',0.00,0.00,0.00,NULL,0,NULL),(91,'2026-01-08','ACVV Riebeek Kasteel (PF101)','PF101',0.00,0.00,0.00,NULL,0,NULL),(92,'2026-01-08','ACVV Riversdal (PF102)','PF102',0.00,0.00,0.00,NULL,0,NULL),(93,'2026-01-08','ACVV Robertson Huis Le Roux (PF103)','PF103',0.00,0.00,0.00,NULL,0,NULL),(94,'2026-01-08','ACVV Robertson (PF104)','PF104',0.00,0.00,0.00,NULL,0,NULL),(95,'2026-01-08','ACVV Rusoord Tehuis vir Oues van Dae Paarl (PF105)','PF105',0.00,0.00,0.00,NULL,0,NULL),(96,'2026-01-08','ACVV Clanwilliam (PF106)','PF106',0.00,0.00,0.00,NULL,0,NULL),(97,'2026-01-08','ACVV Somerset Oos Huis Silwerjare (PF107)','PF107',0.00,0.00,0.00,NULL,0,NULL),(98,'2026-01-08','ACVV Wellington Tak Silwerkruin (PF108)','PF108',0.00,0.00,0.00,NULL,0,NULL),(99,'2026-01-08','ACVV Elizabeth Roos Tehuis Dienstak (PF110)','PF110',0.00,0.00,0.00,NULL,0,NULL),(100,'2026-01-08','ACVV Skiereiland Beheerkomitee van die ACVV Dienstak (PF111)','PF111',0.00,0.00,0.00,NULL,0,NULL),(101,'2026-01-08','ACVV Strand Soeterus Tehuis (PF112)','PF112',0.00,0.00,0.00,NULL,0,NULL),(102,'2026-01-08','ACVV Lambersbaai Somerkoelte Tehuis (PF113)','PF113',0.00,0.00,0.00,NULL,0,NULL),(103,'2026-01-08','ACVV Somerset Wes (PF115)','PF115',0.00,0.00,0.00,NULL,0,NULL),(104,'2026-01-08','ACVV De Aar Sonder Sorge Tehuis (PF117)','PF117',0.00,0.00,0.00,NULL,0,NULL),(105,'2026-01-08','ACVV Calvinia (PF118)','PF118',0.00,0.00,0.00,NULL,0,NULL),(106,'2026-01-08','ACVV Strand Speelkasteel (PF120)','PF120',0.00,0.00,0.00,NULL,0,NULL),(107,'2026-01-08','ACVV Douglas (PF121)','PF121',0.00,0.00,0.00,NULL,0,NULL),(108,'2026-01-08','ACVV Stellenbosch (PF123)','PF123',0.00,0.00,0.00,NULL,0,NULL),(109,'2026-01-08','ACVV Worcester Stilwaters Dienssentrum (PF124)','PF124',0.00,0.00,0.00,NULL,0,NULL),(110,'2026-01-08','ACVV Die Afrikaanse Christelike Vrouevereniging Strand (PF125)','PF125',0.00,0.00,0.00,NULL,0,NULL),(111,'2026-01-08','ACVV Bredasdorp Suideroord Tehuis (PF126)','PF126',0.00,0.00,0.00,NULL,0,NULL),(112,'2026-01-08','ACVV Swellendam (PF127)','PF127',0.00,0.00,0.00,NULL,0,NULL),(113,'2026-01-08','ACVV Middelburg Oos Kaap Huis Karee (PF130)','PF130',0.00,0.00,0.00,NULL,0,NULL),(114,'2026-01-08','ACVV Upington (PF131)','PF131',0.00,0.00,0.00,NULL,0,NULL),(115,'2026-01-08','ACVV Utopia ACVV Tehuis vir Bejaardes Dienstak (PF132)','PF132',0.00,0.00,0.00,NULL,0,NULL),(116,'2026-01-08','ACVV Kirkwood Valleihof Tehuis (PF133)','PF133',0.00,0.00,0.00,NULL,0,NULL),(117,'2026-01-08','ACVV Graaff-Reinet Huis van de Graaff Tehuis (PF134)','PF134',0.00,0.00,0.00,NULL,0,NULL),(118,'2026-01-08','ACVV Huis Van Niekerk Benadehof ACVV Dienssentrum Dienstak (PF135)','PF135',0.00,0.00,0.00,NULL,0,NULL),(119,'2026-01-08','ACVV Huis Vergenoegd Dienstak Diens en Dag (Paarl) (PF136)','PF136',0.00,0.00,0.00,NULL,0,NULL),(120,'2026-01-08','ACVV Huis Vergenoegd Dienstak Siekeboeg (Paarl) (PF137)','PF137',0.00,0.00,0.00,NULL,0,NULL),(121,'2026-01-08','ACVV Huis Vergenoegd Dienstak Woonstelle (Paarl) (PF138)','PF138',0.00,0.00,0.00,NULL,0,NULL),(122,'2026-01-08','ACVV Wellington Tak (PF139)','PF139',0.00,0.00,0.00,NULL,0,NULL),(123,'2026-01-08','ACVV Wellington Tak Fyngoud Dienssentrum (PF140)','PF140',0.00,0.00,0.00,NULL,0,NULL),(124,'2026-01-08','ACVV Paarl Vallei Wielie Walie Creche (PF141)','PF141',0.00,0.00,0.00,NULL,0,NULL),(125,'2026-01-08','ACVV Weskusnessie Dienstak (PF142)','PF142',0.00,0.00,0.00,NULL,0,NULL),(126,'2026-01-08','ACVV Danielskuil (PF143)','PF143',0.00,0.00,0.00,NULL,0,NULL),(127,'2026-01-08','ACVV Victoria Wes Wiekie Wessie Creche (PF144)','PF144',0.00,0.00,0.00,NULL,0,NULL),(128,'2026-01-08','ACVV Worcester (PF145)','PF145',0.00,0.00,0.00,NULL,0,NULL),(129,'2026-01-08','ACVV Ysterplaat Dienstak van die ACVV (PF146)','PF146',0.00,0.00,0.00,NULL,0,NULL),(130,'2026-01-08','ACVV Zonnebloem ACVV Dienstak (PF147)','PF147',0.00,0.00,0.00,NULL,0,NULL),(131,'2026-01-08','ACVV Strand Dienssentrum vir Seniors (PF148)','PF148',0.00,0.00,0.00,NULL,0,NULL),(132,'2026-01-08','ACVV Grabouw Appelkontrei Dienssentrum (PF149)','PF149',0.00,0.00,0.00,NULL,0,NULL),(133,'2026-01-08','ACVV Reivilo Dienssentrum (PF150)','PF150',0.00,0.00,0.00,NULL,0,NULL),(134,'2026-01-08','ACVV Elandsbaai (PF151)','PF151',0.00,0.00,0.00,NULL,0,NULL),(135,'2026-01-08','ACVV Colesberg Old Age Home (PF155)','PF155',0.00,0.00,0.00,NULL,0,NULL),(136,'2026-01-08','ACVV Triomf Child Care Centre (PF156)','PF156',0.00,0.00,0.00,NULL,0,NULL),(137,'2026-01-08','ACVV Barrydale (PF157)','PF157',0.00,0.00,0.00,NULL,0,NULL),(138,'2026-01-08','ACVV Malmesbury Dienssentrum (PF161)','PF161',0.00,0.00,0.00,NULL,0,NULL),(139,'2026-01-08','ACVV Somerset Wes Tinktinkie (PF163)','PF163',0.00,0.00,0.00,NULL,0,NULL),(140,'2026-01-08','ACVV Despatch (PF165)','PF165',0.00,0.00,0.00,NULL,0,NULL),(141,'2026-01-08','ACVV Kuruman Heuwelsig (PF166)','PF166',0.00,0.00,0.00,NULL,0,NULL),(142,'2026-01-08','ACVV Port Elizabeth Sentraal Khayalethu Jeugsentrum (PF168)','PF168',0.00,0.00,0.00,NULL,0,NULL),(143,'2026-01-08','ACVV Piketberg Trippe Trappe (PF169)','PF169',0.00,0.00,0.00,NULL,0,NULL),(144,'2026-01-08','ACVV Robertson Jakaranda Dienssentrum (PF171)','PF171',0.00,0.00,0.00,NULL,0,NULL),(145,'2026-01-08','ACVV Worcester Bollieland Creche (PF172)','PF172',0.00,0.00,0.00,NULL,0,NULL),(146,'2026-01-08','ACVV Moorreesburg Kleuterland (PF173)','PF173',0.00,0.00,0.00,NULL,0,NULL),(147,'2026-01-08','ACVV Moorreesburg (PF174)','PF174',0.00,0.00,0.00,NULL,0,NULL),(148,'2026-01-08','ACVV Dienssentrum Moorreesburg (PF175)','PF175',0.00,0.00,0.00,NULL,0,NULL),(149,'2026-01-08','ACVV Moorreesburg Heuwelsig (PF176)','PF176',0.00,0.00,0.00,NULL,0,NULL),(150,'2026-01-08','ACVV Dysselsdorp Swartberg Dienssentrum (PF181)','PF181',0.00,0.00,0.00,NULL,0,NULL),(151,'2026-01-08','ACVV Dysselsdorp Siembamba Creche (PF182)','PF182',0.00,0.00,0.00,NULL,0,NULL),(152,'2026-01-08','ACVV Yzerfontein','PF183',0.00,0.00,0.00,NULL,0,NULL),(153,'2026-01-08','ACVV Dysselsdorp Shelter (PF184)','PF184',0.00,0.00,0.00,NULL,0,NULL),(154,'2026-01-08','ACVV Riebeek Wes Humanitas (PF050)= PF185 ','PF185',0.00,0.00,0.00,NULL,0,NULL),(155,'2026-01-08','ACVV Port Elizabeth Sentraal (PF091)PF186)','PF186',0.00,0.00,0.00,NULL,0,NULL),(156,'2026-01-08','ACVV Marinerylaan (PF180)','PF180',0.00,0.00,0.00,NULL,0,NULL);
/*!40000 ALTER TABLE `reconciliation_record` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `reconciliation_worksheet`
--

DROP TABLE IF EXISTS `reconciliation_worksheet`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `reconciliation_worksheet` (
  `id` int NOT NULL AUTO_INCREMENT,
  `fiscal_month` date NOT NULL,
  `mg_name` varchar(255) NOT NULL,
  `mg_code` varchar(100) NOT NULL,
  `company_status` varchar(50) DEFAULT 'Active',
  `payment_method` varchar(50) DEFAULT 'Debit Order',
  `last_fiscal_reconciled` varchar(100) DEFAULT NULL,
  `arrears` varchar(255) DEFAULT NULL,
  `member_count_reconciled` int DEFAULT '0',
  `contribution_amount_reconciled` decimal(12,2) DEFAULT '0.00',
  `reconciled_status` varchar(50) DEFAULT 'Unreconciled',
  `date_schedule_received` date DEFAULT NULL,
  `date_confirmed_on_step` date DEFAULT NULL,
  `debit_order_date` date DEFAULT NULL,
  `is_closed` tinyint(1) DEFAULT '0',
  `closed_at` datetime(6) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_fiscal_mg` (`fiscal_month`,`mg_code`)
) ENGINE=InnoDB AUTO_INCREMENT=157 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `reconciliation_worksheet`
--

LOCK TABLES `reconciliation_worksheet` WRITE;
/*!40000 ALTER TABLE `reconciliation_worksheet` DISABLE KEYS */;
INSERT INTO `reconciliation_worksheet` VALUES (1,'2026-01-08','MGC001','Alpha Group','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(2,'2026-01-08','ACVV Aberdeen (PF001)','PF001','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(3,'2026-01-08','ACVV Uitenhage ACVV Dienstak (PF002)','PF002','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(4,'2026-01-08','ACVV Malmesbury Aandskemering (PF003)','PF003','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(5,'2026-01-08','ACVV Piketberg Huis AJ Liebenberg (PF004)','PF004','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(6,'2026-01-08','ACVV Algoapark (PF005)','PF005','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(7,'2026-01-08','ACVV Williston (PF006)','PF006','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(8,'2026-01-08','ACVV Azaleahof ACVV Dienssentrum Dienstak (PF007)','PF007','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(9,'2026-01-08','ACVV Olifantshoek Bergen Rus (PF008)','PF008','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(10,'2026-01-08','ACVV Riebeek Wes Huis Bergsig (PF009)','PF009','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(11,'2026-01-08','ACVV Bothasig Creche Dienstak (PF010)','PF010','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(12,'2026-01-08','ACVV Bredasdorp (PF011)','PF011','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(13,'2026-01-08','ACVV Bredasdorp Suidpunt Diens (PF012)','PF012','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(14,'2026-01-08','ACVV Caledon (PF014)','PF014','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(15,'2026-01-08','ACVV Ceres (PF018)','PF018','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(16,'2026-01-08','ACVV Adelaide (PF019)','PF019','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(17,'2026-01-08','ACVV Cradock (PF020)','PF020','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(18,'2026-01-08','ACVV Britstown (PF021)','PF021','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(19,'2026-01-08','ACVV Carnarvon Huis Danie van Huyssteen (PF022)','PF022','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(20,'2026-01-08','ACVV De Aar (PF023)','PF023','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(21,'2026-01-08','ACVV De Aar Lollapot (PF023B)','PF023B','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(22,'2026-01-08','ACVV De Grendel ACVV Dienstak (PF024)','PF024','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(23,'2026-01-08','ACVV Delft Dienstak (PF025)','PF025','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(24,'2026-01-08','ACVV Despatch  Dienssentrum (PF026)','PF026','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(25,'2026-01-08','ACVV Alexandria (PF027)','PF027','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(26,'2026-01-08','ACVV Tulbagh (PF028)','PF028','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(27,'2026-01-08','ACVV Dysselsdorp (PF031)','PF031','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(28,'2026-01-08','ACVV Edelweiss ACVV Dienssentrum en Wooneenhede Dienstak (PF032)','PF032','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(29,'2026-01-08','ACVV Cradock Elizabeth Jordaan (PF034)','PF034','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(30,'2026-01-08','ACVV Franschhoek Fleur de Lis (PF035)','PF035','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(31,'2026-01-08','ACVV Franschhoek (PF036)','PF036','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(32,'2026-01-08','ACVV Victoria Wes (PF037)','PF037','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(33,'2026-01-08','ACVV Port Elizabeth Wes Huis Genot (PF038)','PF038','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(34,'2026-01-08','ACVV George (PF039)','PF039','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(35,'2026-01-08','ACVV Grabouw (PF040)','PF040','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(36,'2026-01-08','ACVV Grabouw Huis Groenland (PF041)','PF041','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(37,'2026-01-08','ACVV Grahamstad (PF042)','PF042','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(38,'2026-01-08','ACVV Newton Park PE Haas Das Creche (PF043)','PF043','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(39,'2026-01-08','ACVV Caledon Heidehof (PF044)','PF044','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(40,'2026-01-08','ACVV Heidelberg (PF045)','PF045','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(41,'2026-01-08','ACVV Griekwastad (PF046)','PF046','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(42,'2026-01-08','ACVV Beaufort-Wes (PF047)','PF047','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(43,'2026-01-08','ACVV Hoofbestuur (PF048)','PF048','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(44,'2026-01-08','ACVV Pofadder Huis Sophia (PF049)','PF049','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(45,'2026-01-08','ACVV Strand Huis Jan Swart (PF051)','PF051','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(46,'2026-01-08','ACVV Postmasburg Huis Jan Vorster (PF052)','PF052','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(47,'2026-01-08','ACVV Tak Kaapstad (PF053)','PF053','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(48,'2026-01-08','ACVV Kimberley (PF054)','PF054','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(49,'2026-01-08','ACVV Koeberg (PF056)','PF056','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(50,'2026-01-08','ACVV Prins Albert Huis Kweekvallei (PF057)','PF057','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(51,'2026-01-08','ACVV Kuruman (PF058)','PF058','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(52,'2026-01-08','ACVV La Belle ACVV Dienstak (PF059)','PF059','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(53,'2026-01-08','ACVV L Amour Martinelle Creche (PF060)','PF060','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(54,'2026-01-08','ACVV Magnolia ACVV Dienstak (PF062)','PF062','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(55,'2026-01-08','ACVV Huis Malan Jacobs ACVV Tehuis vir Bejaardes (PF063)','PF063','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(56,'2026-01-08','ACVV Malmesbury (PF064)','PF064','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(57,'2026-01-08','ACVV Somerset Wes Huis Marie Louw (PF065)','PF065','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(58,'2026-01-08','ACVV Ceres Huis Maudie Kriel (PF066)','PF066','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(59,'2026-01-08','ACVV Middelburg Oos-Kaap (PF067)','PF067','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(60,'2026-01-08','ACVV Kuruman Mimosahof (PF068)','PF068','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(61,'2026-01-08','ACVV Mitchells Plain (PF069)','PF069','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(62,'2026-01-08','ACVV Montagu (PF070)','PF070','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(63,'2026-01-08','ACVV Moorreesburg (PF071)','PF071','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(64,'2026-01-08','ACVV Moreson ACVV Kinder- en Jeugsorgsentrum (PF072)','PF072','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(65,'2026-01-08','ACVV Mosselbaai (PF073)','PF073','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(66,'2026-01-08','ACVV Springbok Huis Namakwaland (PF074)','PF074','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(67,'2026-01-08','ACVV Despatch Huis Najaar (PF075)','PF075','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(68,'2026-01-08','ACVV Porterville Tak Huis Nerina (PF076)','PF076','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(69,'2026-01-08','ACVV Dordrecht (PF077)','PF077','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(70,'2026-01-08','ACVV Worcester (PF078)','PF078','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(71,'2026-01-08','ACVV Paarl Vallei Oase Dienssentrum (PF079)','PF079','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(72,'2026-01-08','ACVV Kimberley Ons Huis (PF080)','PF080','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(73,'2026-01-08','ACVV Ons Tuiste ACVV Dienstak (PF081)','PF081','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(74,'2026-01-08','ACVV Op die Kruin ACVV Dienstak (PF082)','PF082','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(75,'2026-01-08','ACVV Upington Oranjehof Tehuis (PF083)','PF083','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(76,'2026-01-08','ACVV Oudtshoorn (PF085)','PF085','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(77,'2026-01-08','ACVV Paarl (PF086)','PF086','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(78,'2026-01-08','ACVV Noorder-Paal (PF087)','PF087','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(79,'2026-01-08','ACVV Paarl Vallei (PF088)','PF088','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(80,'2026-01-08','ACVV Newton Park PE (PF089)','PF089','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(81,'2026-01-08','ACVV PE Noord (PF090)','PF090','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(82,'2026-01-08','ACVV Port Elizabeth Suid (PF092)','PF092','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(83,'2026-01-08','ACVV Port Elizabeth Wes (PF093)','PF093','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(84,'2026-01-08','ACVV Piketberg (PF094)','PF094','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(85,'2026-01-08','ACVV St Helenabaai (PF095)','PF095','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(86,'2026-01-08','ACVV Poplarlaan PE (PF096)','PF096','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(87,'2026-01-08','ACVV Porterville Tak (PF097)','PF097','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(88,'2026-01-08','ACVV Postmasburg (PF098)','PF098','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(89,'2026-01-08','ACVV Prieska (PF099)','PF099','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(90,'2026-01-08','ACVV Caledon Protea Dienssentrum (PF100)','PF100','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(91,'2026-01-08','ACVV Riebeek Kasteel (PF101)','PF101','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(92,'2026-01-08','ACVV Riversdal (PF102)','PF102','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(93,'2026-01-08','ACVV Robertson Huis Le Roux (PF103)','PF103','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(94,'2026-01-08','ACVV Robertson (PF104)','PF104','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(95,'2026-01-08','ACVV Rusoord Tehuis vir Oues van Dae Paarl (PF105)','PF105','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(96,'2026-01-08','ACVV Clanwilliam (PF106)','PF106','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(97,'2026-01-08','ACVV Somerset Oos Huis Silwerjare (PF107)','PF107','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(98,'2026-01-08','ACVV Wellington Tak Silwerkruin (PF108)','PF108','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(99,'2026-01-08','ACVV Elizabeth Roos Tehuis Dienstak (PF110)','PF110','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(100,'2026-01-08','ACVV Skiereiland Beheerkomitee van die ACVV Dienstak (PF111)','PF111','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(101,'2026-01-08','ACVV Strand Soeterus Tehuis (PF112)','PF112','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(102,'2026-01-08','ACVV Lambersbaai Somerkoelte Tehuis (PF113)','PF113','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(103,'2026-01-08','ACVV Somerset Wes (PF115)','PF115','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(104,'2026-01-08','ACVV De Aar Sonder Sorge Tehuis (PF117)','PF117','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(105,'2026-01-08','ACVV Calvinia (PF118)','PF118','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(106,'2026-01-08','ACVV Strand Speelkasteel (PF120)','PF120','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(107,'2026-01-08','ACVV Douglas (PF121)','PF121','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(108,'2026-01-08','ACVV Stellenbosch (PF123)','PF123','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(109,'2026-01-08','ACVV Worcester Stilwaters Dienssentrum (PF124)','PF124','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(110,'2026-01-08','ACVV Die Afrikaanse Christelike Vrouevereniging Strand (PF125)','PF125','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(111,'2026-01-08','ACVV Bredasdorp Suideroord Tehuis (PF126)','PF126','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(112,'2026-01-08','ACVV Swellendam (PF127)','PF127','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(113,'2026-01-08','ACVV Middelburg Oos Kaap Huis Karee (PF130)','PF130','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(114,'2026-01-08','ACVV Upington (PF131)','PF131','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(115,'2026-01-08','ACVV Utopia ACVV Tehuis vir Bejaardes Dienstak (PF132)','PF132','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(116,'2026-01-08','ACVV Kirkwood Valleihof Tehuis (PF133)','PF133','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(117,'2026-01-08','ACVV Graaff-Reinet Huis van de Graaff Tehuis (PF134)','PF134','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(118,'2026-01-08','ACVV Huis Van Niekerk Benadehof ACVV Dienssentrum Dienstak (PF135)','PF135','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(119,'2026-01-08','ACVV Huis Vergenoegd Dienstak Diens en Dag (Paarl) (PF136)','PF136','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(120,'2026-01-08','ACVV Huis Vergenoegd Dienstak Siekeboeg (Paarl) (PF137)','PF137','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(121,'2026-01-08','ACVV Huis Vergenoegd Dienstak Woonstelle (Paarl) (PF138)','PF138','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(122,'2026-01-08','ACVV Wellington Tak (PF139)','PF139','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(123,'2026-01-08','ACVV Wellington Tak Fyngoud Dienssentrum (PF140)','PF140','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(124,'2026-01-08','ACVV Paarl Vallei Wielie Walie Creche (PF141)','PF141','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(125,'2026-01-08','ACVV Weskusnessie Dienstak (PF142)','PF142','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(126,'2026-01-08','ACVV Danielskuil (PF143)','PF143','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(127,'2026-01-08','ACVV Victoria Wes Wiekie Wessie Creche (PF144)','PF144','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(128,'2026-01-08','ACVV Worcester (PF145)','PF145','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(129,'2026-01-08','ACVV Ysterplaat Dienstak van die ACVV (PF146)','PF146','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(130,'2026-01-08','ACVV Zonnebloem ACVV Dienstak (PF147)','PF147','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(131,'2026-01-08','ACVV Strand Dienssentrum vir Seniors (PF148)','PF148','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(132,'2026-01-08','ACVV Grabouw Appelkontrei Dienssentrum (PF149)','PF149','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(133,'2026-01-08','ACVV Reivilo Dienssentrum (PF150)','PF150','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(134,'2026-01-08','ACVV Elandsbaai (PF151)','PF151','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(135,'2026-01-08','ACVV Colesberg Old Age Home (PF155)','PF155','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(136,'2026-01-08','ACVV Triomf Child Care Centre (PF156)','PF156','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(137,'2026-01-08','ACVV Barrydale (PF157)','PF157','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(138,'2026-01-08','ACVV Malmesbury Dienssentrum (PF161)','PF161','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(139,'2026-01-08','ACVV Somerset Wes Tinktinkie (PF163)','PF163','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(140,'2026-01-08','ACVV Despatch (PF165)','PF165','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(141,'2026-01-08','ACVV Kuruman Heuwelsig (PF166)','PF166','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(142,'2026-01-08','ACVV Port Elizabeth Sentraal Khayalethu Jeugsentrum (PF168)','PF168','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(143,'2026-01-08','ACVV Piketberg Trippe Trappe (PF169)','PF169','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(144,'2026-01-08','ACVV Robertson Jakaranda Dienssentrum (PF171)','PF171','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(145,'2026-01-08','ACVV Worcester Bollieland Creche (PF172)','PF172','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(146,'2026-01-08','ACVV Moorreesburg Kleuterland (PF173)','PF173','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(147,'2026-01-08','ACVV Moorreesburg (PF174)','PF174','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(148,'2026-01-08','ACVV Dienssentrum Moorreesburg (PF175)','PF175','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(149,'2026-01-08','ACVV Moorreesburg Heuwelsig (PF176)','PF176','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(150,'2026-01-08','ACVV Dysselsdorp Swartberg Dienssentrum (PF181)','PF181','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(151,'2026-01-08','ACVV Dysselsdorp Siembamba Creche (PF182)','PF182','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(152,'2026-01-08','ACVV Yzerfontein','PF183','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(153,'2026-01-08','ACVV Dysselsdorp Shelter (PF184)','PF184','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(154,'2026-01-08','ACVV Riebeek Wes Humanitas (PF050)= PF185 ','PF185','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(155,'2026-01-08','ACVV Port Elizabeth Sentraal (PF091)PF186)','PF186','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL),(156,'2026-01-08','ACVV Marinerylaan (PF180)','PF180','Active','Debit Order',NULL,NULL,0,0.00,'Unreconciled',NULL,NULL,NULL,0,NULL);
/*!40000 ALTER TABLE `reconciliation_worksheet` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `temp_exit`
--

DROP TABLE IF EXISTS `temp_exit`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `temp_exit` (
  `id` int NOT NULL AUTO_INCREMENT,
  `mg_code` varchar(50) NOT NULL,
  `surname` varchar(255) NOT NULL,
  `initials` varchar(50) DEFAULT NULL,
  `mip_no` varchar(100) DEFAULT NULL,
  `id_no` varchar(13) DEFAULT NULL,
  `reason` varchar(255) DEFAULT NULL,
  `bis_from_date` date DEFAULT NULL,
  `bis_end_date` date DEFAULT NULL,
  `full_contributions_start_date` date DEFAULT NULL,
  `note` text,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `temp_exit`
--

LOCK TABLES `temp_exit` WRITE;
/*!40000 ALTER TABLE `temp_exit` DISABLE KEYS */;
/*!40000 ALTER TABLE `temp_exit` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-01-20 15:17:51
