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
INSERT INTO `acvv_outlook_token` VALUES (1,'testuser@futurasa.co.za','eyJ0eXAiOiJKV1QiLCJub25jZSI6IlFIb3VCUEhjOXhmcWwzbVlRYkNEWExkaXE2cTVIcmMtS19ibzZjRExqek0iLCJhbGciOiJSUzI1NiIsIng1dCI6InJ0c0ZULWItN0x1WTdEVlllU05LY0lKN1ZuYyIsImtpZCI6InJ0c0ZULWItN0x1WTdEVlllU05LY0lKN1ZuYyJ9.eyJhdWQiOiJodHRwczovL2dyYXBoLm1pY3Jvc29mdC5jb20iLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC83YmNmYzA4MC1lMWYxLTRmOTktYjRlZC1lMWE5NmVkYTg5Y2UvIiwiaWF0IjoxNzY1NTMyMTIxLCJuYmYiOjE3NjU1MzIxMjEsImV4cCI6MTc2NTUzNjAyMSwiYWlvIjoiazJKZ1lPQTJVNjE3YzJheTNrU3VId3F6TlN0REFRPT0iLCJhcHBfZGlzcGxheW5hbWUiOiJGdXR1cmEtQXBwIiwiYXBwaWQiOiI5ZjgyZTU3ZC00NWE0LTRiNjYtYWIyOS04YTliMzgxYTA4MmEiLCJhcHBpZGFjciI6IjEiLCJpZHAiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC83YmNmYzA4MC1lMWYxLTRmOTktYjRlZC1lMWE5NmVkYTg5Y2UvIiwiaWR0eXAiOiJhcHAiLCJvaWQiOiI0MTc2NDgyNy0yZGJlLTRiMTYtYWJhNi0xZDIwMDYxYjU5MWYiLCJyaCI6IjEuQVNBQWdNRFBlX0hobVUtMDdlR3BidHFKemdNQUFBQUFBQUFBd0FBQUFBQUFBQUE5QVFBZ0FBLiIsInJvbGVzIjpbIk1haWwuUmVhZCIsIk1haWwuU2VuZCJdLCJzdWIiOiI0MTc2NDgyNy0yZGJlLTRiMTYtYWJhNi0xZDIwMDYxYjU5MWYiLCJ0ZW5hbnRfcmVnaW9uX3Njb3BlIjoiQUYiLCJ0aWQiOiI3YmNmYzA4MC1lMWYxLTRmOTktYjRlZC1lMWE5NmVkYTg5Y2UiLCJ1dGkiOiJISmlJaWdna0MwZWpROUswR2FKU0FBIiwidmVyIjoiMS4wIiwid2lkcyI6WyIwOTk3YTFkMC0wZDFkLTRhY2ItYjQwOC1kNWNhNzMxMjFlOTAiXSwieG1zX2FjZCI6MTc2NDE2MDkyNiwieG1zX2FjdF9mY3QiOiIzIDkiLCJ4bXNfZnRkIjoiTkJsM3RFckMyRzRRX0xvM2VPOTlwYnNpaDFsQVlxejNzU3Z6ZVBPYlFYOEJjM2RsWkdWdVl5MWtjMjF6IiwieG1zX2lkcmVsIjoiMTYgNyIsInhtc19yZCI6IjAuNDJMbFlCSmlWQkFTNFdBWEV2aFM4X2Ria2R4T3g1bF9jajdPVU42bUJ4VGxGQko0MjVBY0Z0TFQ3RDVkZ2VGMVdWbXRMMUNVUTBpQW1RRUNEa0JwQUEiLCJ4bXNfc3ViX2ZjdCI6IjkgMyIsInhtc190Y2R0IjoxNDk5NzEyNDIwLCJ4bXNfdG50X2ZjdCI6IjMgMTYifQ.dqbRxEAdPf6XJGtnQF9pl-ktaQeeCfRlX2rDcfkK8LL1-4aUCdcaf4GHRbIdI075UdfSFjFlFBNPK5VrmUfBFbPGvOpj9nTeIMO2lzd8WSxLOFl14vj2sKDgrVGIjF9d2hmP0EZHkKCvLLIshA7OPqzC7D1JXmflV9_vvqzaJvHODuCIefLDUzGsQNtwEClaIiWWLRZnU0pzoovOKLh-vNITTVqCp0ocM1J9DAOCJ_dw4cMCDtONfukHMmC6J311dxdyGdn4odZphsvlvdURk8dh5tLsdK83l9RfSqpfmXp79OeYkoxyovxP3AIqmRC9xe07GBnMVGLGecty-G0SMw',NULL,3599,'2025-12-12 09:40:23.584433');
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
INSERT INTO `auth_user` VALUES (1,'pbkdf2_sha256$1000000$0zg9UjZB2zeXSXInM9C3Md$igTZw8J2jh3znUITqGVLWa7Rnm0XOjrpqtc21GO/uQs=','2025-12-12 10:24:06.111206',1,'omega','','','',1,1,'2025-09-19 11:24:27.343696'),(2,'pbkdf2_sha256$1000000$dmFBjFd3XWtYQDePDKE1qQ$VbHMeUILJFaR9aZ7eTTIm3qpJmz2ixVbAlv+hbMLrNA=','2025-12-11 09:31:18.620642',0,'testuser','','','test@example.com',0,1,'2025-12-11 08:24:58.760332'),(3,'pbkdf2_sha256$1000000$A6jOIWZeJPKi5HOwLb1Lxv$bjhJFbJALlW79g9YGYS9xhIDlHvbo0DsAGglo9TlvRY=',NULL,0,'testuser1','','','',0,1,'2025-12-17 09:59:07.678369'),(4,'pbkdf2_sha256$1000000$7SPlHWZzImqF6bgXpBsmQf$JAfm9A/lxtXqSjfM/oU/o8yeZ264hgAqzS+VzhUOvCI=',NULL,0,'testuser2','','','',0,1,'2025-12-17 09:59:08.012316'),(5,'pbkdf2_sha256$1000000$VuhW8ZRFtGZyuKEXYsom32$6DFdB0pUijLFEZ3xbOBy/ROb4tKl0Z+4MDPulqVzPhM=',NULL,0,'testuser3','','','',0,1,'2025-12-17 09:59:08.337488'),(6,'pbkdf2_sha256$1000000$OBszZ7dhhdPgkL7xuTC2h3$dw2k2ERlcYoHZRZvUNsRrizQGT7XAI+FiHpdafrNK1Q=',NULL,0,'testuser4','','','',0,1,'2025-12-17 09:59:08.662876');
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
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `client_notes`
--

LOCK TABLES `client_notes` WRITE;
/*!40000 ALTER TABLE `client_notes` DISABLE KEYS */;
INSERT INTO `client_notes` VALUES (1,'Koos','2025-09-23 00:00:00','Roos','I want to Mr.Koos a Roos'),(2,'MGC001','2025-09-23 00:00:00','Roos','I want to buy Mr.Koos a Roos'),(3,'MGC001','2025-09-23 10:57:52','omega','Hello Koos');
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
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `delegation_note`
--

LOCK TABLES `delegation_note` WRITE;
/*!40000 ALTER TABLE `delegation_note` DISABLE KEYS */;
INSERT INTO `delegation_note` VALUES (1,5,1,'Delegated to testuser. Category: , MIP: None','2025-12-11 08:30:55.995685'),(2,8,1,'Delegated to testuser. Category: LPI, MIP: None','2025-12-11 09:14:09.034607');
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
INSERT INTO `django_session` VALUES ('018qwmxfyz2tadifujxw32jbr2xdq22e','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1v0c12:DjtpoiIKLphnUVFzKC0tiW1E9hkxCUoRrWB5H89vcgk','2025-10-06 08:35:20.587529'),('2d9fjhdj825wf38ekhrvjb409r0e732c','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1v0fqL:2FyIHs5Le40E47vCzkPYoEvmn8hBjE5zPbrgXv8IK3o','2025-10-06 12:40:33.162859'),('2kb9wbxsis1qm9ekdf68hhbgmxjyvcgy','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vOcjg:vAkru7Z6gEo4aQ8h3D2c6aYCu09qKSw9fbhRfAmjr8Q','2025-12-11 14:12:40.542000'),('2ryh8ntcvu5wa5oqbtzgnlhyj54i2fwr','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1v1ibn:G8ikhiVtjwxWTg61pMWtrF_NZF1qcMChCXARzXSm_5Y','2025-10-09 09:49:51.511498'),('32mafyj110632k3okrl2qroai0nvka9b','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1v4FNz:cvj2_s4RMSAnZ6Qh_T8_0LlzZpjBc8Uwg_UoS0pnYcI','2025-10-16 09:14:03.408365'),('4xbr8ql7tz59l7ai1as2p4vg03zltw5b','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1v0gmE:HwnFn3kixVObykipbhUzbVUeOSIFaZt4DdcyuuY4rmU','2025-10-06 13:40:22.320585'),('7fjpfeffsdxsc1s2dzoqsufzzdwvvdq7','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vSxQ8:CtS9xsPBwh9Txo9AaIziVwItG5Kgp2sEa2vR0bvrNMA','2025-12-23 13:06:24.768193'),('apeiyv097esg2dmaajdgqbkia26ic0nt','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1v0aqe:FpyzmyU0o9IoVUrFsxZBCooF0oyp2kyt0OCNkL6zRB0','2025-10-06 07:20:32.380066'),('dq5b08w0ntrcvn7y7470gznp6l0tzixw','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1v0xrk:Bqo8CuLED0d_ZlDP436cSojDNkm5SlbpJvhzIksBaXo','2025-10-07 07:55:12.318694'),('fpbvp5qlrfs8ygbpyal9ly6x07a4hmp2','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1v0zVK:OSishOOoLAFS_aNFM1okDciqibEqZvicCBvvjHBoo5M','2025-10-07 09:40:10.535461'),('hqvhhrwpbuw3dw152yp518naoa2zlij7','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vTPJ5:1I40ajLXJHOS2ukCbNdaAMyJ2kto5hloI_UCX8mQDXE','2025-12-24 18:52:59.836797'),('kiz2zhkcusp1k65kv6rsode2msfaumu6','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1v0dUE:doUpjmxx1WXqkkxLr8nv9eZgIYZbhmZI7blriWLNCjk','2025-10-06 10:09:34.546298'),('lycdf2q5duoakuhxghcc2hd7yn8x3ue9','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1v0gSJ:SRpDIBo029DoNWsKe-Q2W8nPFpKX_GpiA_1G6VhqT6U','2025-10-06 13:19:47.032976'),('pyap4iqiyseo70dnoxfm9hygswbe7sfh','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vU0Ji:wMJ49uYEZOf0_kWjkIY_ZAeju61yVJC5iest0AG4VSE','2025-12-26 10:24:06.124490'),('simb3r12rgyr8lyy6royse3u4c8qr3rq','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vTzdM:9wuzMlBa6bGyMvCvtZigtkHJZ09LVRZAmHkaIaqFOQ8','2025-12-26 09:40:20.342925'),('suy2xw9ouz532todnxfb8qofpqeqrqwe','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1v0xMf:MowAagjOHf8PBQDiMi6LLPerDuS2-njF8CdhH469F4o','2025-10-07 07:23:05.991425'),('up4qygzkowha3kmjfvsn7fs4ayvg94ej','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1v1lGF:wEqh0uEhgMqw1AG7dE-B9XRCi7QIXbs1Y27cSK4ypZM','2025-10-09 12:39:47.986746'),('us28ktm45qwazizmt1ezgiq5jldg8haf','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vSuYU:viUwCEgQcBfrWlUCEmAyiKRBTtguQMNW8Y5UpMCZd3s','2025-12-23 10:02:50.618457'),('vbfhssrrzxdojbouaupitr4wzgyw5p14','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1uzZWX:Brx_PkMem2FfqyDBvEaUYkLC_aEkvZa0xubReKj-JiQ','2025-10-03 11:43:33.944470'),('xr9f4th80uj5lcqhsr4nfo87oilfyidj','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vTdAO:R9TNTirEzApyVlMbaSiTAwk8bWaEJbyEUOL8CvPSq60','2025-12-25 09:40:56.210810');
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
  `assigned_user_id` int DEFAULT NULL,
  `status` varchar(3) NOT NULL,
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
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `email_delegation`
--

LOCK TABLES `email_delegation` WRITE;
/*!40000 ALTER TABLE `email_delegation` DISABLE KEYS */;
INSERT INTO `email_delegation` VALUES (1,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAIMinLAAA=',NULL,'NEW',NULL,1,NULL,NULL,NULL,NULL),(2,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAIMinKAAA=',NULL,'NEW',NULL,1,NULL,NULL,NULL,NULL),(3,'AQMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAADxCdhLTQUWk2W-CG7KM1O1AcAbvw1wagjFUmX5m7fswwk9QAAAgEMAAAAbvw1wagjFUmX5m7fswwk9QAAAgVcAAAA',NULL,'NEW',NULL,1,NULL,NULL,NULL,NULL),(4,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAIMinMAAA=',NULL,'NEW',NULL,1,NULL,NULL,NULL,NULL),(5,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAIhY0BAAA=',2,'DEL','2025-12-11 08:30:55.990611',1,'','Email','',NULL),(6,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAIhY0CAAA=',NULL,'NEW',NULL,1,NULL,NULL,NULL,NULL),(7,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAIhY0DAAA=',NULL,'NEW',NULL,1,NULL,NULL,NULL,NULL),(8,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAIhY0EAAA=',2,'DEL','2025-12-11 09:14:09.031836',1,'LPI','Email','','2025-12-11 09:13:39.000000'),(9,'AAMkAGZjYjdiOTRmLTE2NzUtNGZjOC05ZGFjLTg2ZDg5Njg5MWM0YgBGAAAAAADEJ2EtNBRaTZb8IbsozU7UBwBu-DXBqCMVSZfmbt_zDCT1AAAAAAEMAABu-DXBqCMVSZfmbt_zDCT1AAAJIxmVAAA=',NULL,'NEW',NULL,1,NULL,NULL,NULL,'2025-12-12 10:25:09.000000');
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
INSERT INTO `global acvv` VALUES ('MGC001','Alpha Group','Box','Active','PO Box 1234, Cityville','Box','123 Main Street, Cityville','Box','Box','Box','Box'),('ACVV Aberdeen (PF001)','PF001','17','Done','13934,98','01.10.2024','','05.10.2024','Successful','Aalwynhof <aalwynhofacvv@gmail.com>',''),('ACVV Uitenhage ACVV Dienstak (PF002)','PF002','78','Done','70233,17','16.09.2024','100% update member info on RFW','27.09.2024','Successful','Aandmymering Tehuis vir Bejaardes <acvvaandmymering@acvv.org.za>','041 – 9921510'),('ACVV Malmesbury Aandskemering (PF003)','PF003','49','Done','57462,55','25.09.2024','RECEIVED LID INFO upload when SEP is open','27.09.2024','Successful','Personeel <personeel@cornergate.com>','022 482 1466'),('ACVV Piketberg Huis AJ Liebenberg (PF004)','PF004','23','Done','21715,49','04.10.2024','','07.10.2024','Successful','Lana Henrico <payroll@ro.co.za>;manager@hajl.co.za ; Wilma Mouton <Wilma@quattrocitrus.co.za> ;Marelise Vercuiel <marelisevercuiel@gmail.com>',''),('ACVV Algoapark (PF005)','PF005','8','Done','16601,25','27.09.2024','RECEIVED LID INFO upload when SEP is open','01.10.2024','Successful','Colleen Woods <acvvcwoods@gmail.com>',''),('ACVV Williston (PF006)','PF006','11','Done','9286,5','16.09.2024','100% update member info on RFW','25.09.2024','Successful','Amandelhof Kotie Hugo <finans.amandel@hantam.co.za>','053 – 3913 185'),('ACVV Azaleahof ACVV Dienssentrum Dienstak (PF007)','PF007','32','Done','54218,7','04.10.2024','100% update member info on RFW','07.10.2024','Successful','azaleahofacc@adept.co.za',''),('ACVV Olifantshoek Bergen Rus (PF008)','PF008','29','Done','22599,6','25.09.2024','','30.09.2024','','AJ Roelofse <ajroelofse2@gmail.com>',''),('ACVV Riebeek Wes Huis Bergsig (PF009)','PF009','29','Done','31141,53','25.09.2024','100% update member info on RFW','27.09.2024','Partially successful','fin.huisbergsig@acvv.org.za','022-461 2721'),('ACVV Bothasig Creche Dienstak (PF010)','PF010','18','Done','17323,8','25.09.2024','100% update member info on RFW','30.09.2024','Successful','Antoinette Brand <antoinettebrand775@gmail.com>','021-558-4314'),('ACVV Bredasdorp (PF011)','PF011','1','Done','1170,9','27.09.2024','100% update member info on RFW','30.09.2024','Successful','Corrali Groenewald <rekeninge1@suideroord.co.za>','028 424 1080 '),('ACVV Bredasdorp Suidpunt Diens (PF012)','PF012','2','Done','2997,3','27.09.2024','100% update member info on RFW','30.09.2024','Successful','Corrali Groenewald <rekeninge1@suideroord.co.za>','028 424 1080 '),('ACVV Caledon (PF014)','PF014','10','Done','11100,15','23.09.2024','100% update member info on RFW','30.09.2024','Successful','Rocksand Kellerman <fin.acvvdagsorg@gmail.com> ; finans.heidehof@twk.co.za','(023) 316 1505'),('ACVV Ceres (PF018)','PF018','4','Done','9036,75','27.09.2024','100% update member info on RFW','28.09.2024','Successful','fin.ceres@acvv.org.za',''),('ACVV Adelaide (PF019)','PF019','33','Done','21327,96','25.09.2024','100% update member info on RFW','27.09.2024','Successful','Aurelia Loots <aurelialoots@yahoo.com>',''),('ACVV Cradock (PF020)','PF020','9','Done','9978,34','26.09.2024','100% update member info on RFW','04.10.2024','Successful','ACVV Cradock <cradock@acvv.org.za>',''),('ACVV Britstown (PF021)','PF021','14','Done','9160,24','02.10.2024','100% update member info on RFW','07.10.2024','Successful','HUIS DANEEL ADMIN <acvvhuisdaneel@gmail.com>',''),('ACVV Carnarvon Huis Danie van Huyssteen (PF022)','PF022','14','Done','10701,16','30.09.2024','100% update member info on RFW','04.10.2024','Successful','Huis Danie van Huyssteen <huisdanie003805@gmail.com>',''),('ACVV De Aar (PF023)','PF023','4','Done','3300','02.10.2024','100% update member info on RFW','03.10.2024','Successful','ACVV De Aar <fin.acvvdeaar@acvv.org.za>','064 982 8803'),('ACVV De Aar Lollapot (PF023B)','PF023B','8','Done','8033,19','26.09.2024','100% update member info on RFW','27.09.2024','','Elzaan Fourie <elzaan@deaarsa.co.za>',''),('ACVV De Grendel ACVV Dienstak (PF024)','PF024','16','Done','13418,31','27.09.2024','100% update member info on RFW','28.09.2024','Successful','Mandy White <acvvdegrendel@acvv.org.za>',''),('ACVV Delft Dienstak (PF025)','PF025','8','Done','7075,2','16.09.2024','100% update member info on RFW','19.09.2024','Successful','Labelle <acvvlabelle-fin@acvv.org.za>','021 948 2019'),('ACVV Despatch  Dienssentrum (PF026)','PF026','2','Done','1353,28','04.10.2024','100% update member info on RFW','05.10.2024','','ACVV Dienssentrum <dienssentrum2@telkomsa.net>',''),('ACVV Alexandria (PF027)','PF027','32','Done','27603','26.09.2024','','30.09.2024','','ACVV Huis Diaz <fin.huisdiaz@acvv.org.za>',''),('ACVV Tulbagh (PF028)','PF028','18','Done','21065,31','27.09.2024','100% update member info on RFW','04.10.2024','Successful','ACVV Huis Disa <bestuurder.huisdisa@acvv.org.za> ; fin.huisdisa@acvv.org.za',''),('ACVV Dysselsdorp (PF031)','PF031','6','Done','7765,84','01.10.2024','100% update member info on RFW','02.10.2024','','acvvfinansies@scwireless.co.za','044 251 6721 / 062 405 4918'),('ACVV Edelweiss ACVV Dienssentrum en Wooneenhede Dienstak (PF032)','PF032','20','Done','30564','23.09.2024','100% update member info on RFW','26.09.2024','Successful','Edelweiss ACVV <acvvedelweiss@acvv.org.za>','021 9761150'),('ACVV Cradock Elizabeth Jordaan (PF034)','PF034','37','Done','36363,09','27.09.2024','100% update member info on RFW','30.09.2024','Successful','EJT Finansies <fin.ejtehuis@acvv.org.za>','048 8811857'),('ACVV Franschhoek Fleur de Lis (PF035)','PF035','20','Done','20167,2','28.09.2024','100% update member info on RFW','01.10.2024','','fin.acvvfleur@acvv.org.za ; admin@acvvfleur.co.za','021-8762411'),('ACVV Franschhoek (PF036)','PF036','2','Done','4493,08','25.09.2024','100% update member info on RFW','30.09.2024','','sandra@wemz.co.za ; admin@acvvfrans.org.za ; fin@acvvfrans.org.za','021 0231298'),('ACVV Victoria Wes (PF037)','PF037','16','Done','10031,39','28.09.2024','','01.10.2024','Successful','Christina Steenkamp <vicwesacvv2@gmail.com>;Denise Els <elsdenise3@gmail.com>',''),('ACVV Port Elizabeth Wes Huis Genot (PF038)','PF038','41','Done','37080,2','26.09.2024','','30.09.2024','Successful','ACVV Huis Genot <fin.huisgenot@acvv.org.za>',''),('ACVV George (PF039)','PF039','47','Done','65468,57','01.10.2024','100% update member info on RFW','03.10.2024','Successful','Accounts <accountsgrg@acvv.org.za>',''),('ACVV Grabouw (PF040)','PF040','7','Done','16364,56','17.09.2024','100% update member info on RFW','30.09.2024','Successful','fin.huisgroenland@acvv.org.za ; manager@huisgroenland.co.za','021 859 4209'),('ACVV Grabouw Huis Groenland (PF041)','PF041','19','Done','26730','17.09.2024','100% update member info on RFW','30.09.2024','Successful','fin.huisgroenland@acvv.org.za ; manager@huisgroenland.co.za','021 859 4209'),('ACVV Grahamstad (PF042)','PF042','5','Done','4204,74','30.09.2024','100% update member info on RFW','07.10.2024','Successful','ACVV Senior Citizens <fin.grahamstad@acvv.org.za>',''),('ACVV Newton Park PE Haas Das Creche (PF043)','PF043','13','Done','10325,34','01.10.2024','100% update member info on RFW','03.10.2024','Successful','Johannes Petrus Beukman <johanbeukman.irispark@gmail.com>',''),('ACVV Caledon Heidehof (PF044)','PF044','31','Done','38783,25','26.09.2024','100% update member info on RFW','30.09.2024','Successful','finans.heidehof@twk.co.za','028 214 1755'),('ACVV Heidelberg (PF045)','PF045','2','Done','1952,1','27.09.2024','100% update member info on RFW','30.09.2024','Successful','Anne-Marié Keyser <hshfinansies@gmail.com>','028 7221 384'),('ACVV Griekwastad (PF046)','PF046','13','Done','10075,8','23.09.2024','100% update member info on RFW','01.10.2024','Successful','Huis Heldersig <huisheldersig@yahoo.co.za>','053 343 0228'),('ACVV Beaufort-Wes (PF047)','PF047','49','Done','44817','25.09.2024','100% update member info on RFW','27.09.2024','Successful','ACVV Hesperos <acvvhesperos@beaufortwest.net>','023-414-3465'),('ACVV Hoofbestuur (PF048)','PF048','27','Done','118812,92','26.09.2024','100% update member info on RFW','28.09.2024','Successful','andre@acvv.org.za','021-461-7437'),('ACVV Pofadder Huis Sophia (PF049)','PF049','17','Done','14474,45','02.10.2024','','04.10.2024','Successful','Huis Sophia <acvvsophiatehuis@acvv.org.za>','054 933 0297'),('ACVV Strand Huis Jan Swart (PF051)','PF051','20','Done','25294,2','30.09.2024','100% update member info on RFW','02.10.2024','Successful','Boekhouer Huis Jan Swart <accounts@huisjs.co.za>','021 854-3763'),('ACVV Postmasburg Huis Jan Vorster (PF052)','PF052','16','Done','15161,39','04.10.2024','','05.10.2024','','Ronel Dippenaar <roneldip@gmail.com> ; ACVV HuisJanVorster <huisjanvorster@outlook.com>',''),('ACVV Tak Kaapstad (PF053)','PF053','25','','53952,99','','','','Successful','accounts@acvvct.org.za',''),('ACVV Kimberley (PF054)','PF054','3','Done','5008,74','30.09.2024','100% update member info on RFW','01.10.2024','Successful','frans@acvv-kimberley.co.za','053 842 1141'),('ACVV Koeberg (PF056)','PF056','6','Done','13233','25.09.2024','','27.09.2024','Successful','dawnsutton397@gmail.com ; acvvkoeberg@acvv.org.za','021-553-2745'),('ACVV Prins Albert Huis Kweekvallei (PF057)','PF057','23','Done','23175,9','26.09.2024','100% update member info on RFW','04.10.2024','','Munnik <munnik@evolveaa.co.za>','051-410-4200'),('ACVV Kuruman (PF058)','PF058','1','Done','260,4','16.09.2024','100% update member info on RFW','27.09.2024','Successful','ACVV Kuruman <kuruman@acvv.org.za>','0537121862 / 0537121341'),('ACVV La Belle ACVV Dienstak (PF059)','PF059','18','Done','26235,84','16.09.2024','100% update member info on RFW','19.09.2024','Successful','Labelle <acvvlabelle-fin@acvv.org.za>','021 948 2019'),('ACVV L Amour Martinelle Creche (PF060)','PF060','1','Done','1012,5','26.09.2024','100% update member info on RFW','28.09.2024','','Maryna Collins <Lamourm@wo.co.za>',''),('ACVV Magnolia ACVV Dienstak (PF062)','PF062','32','Done','44582,55','19.09.2024','100% update member info on RFW','30.09.2024','Successful','Margherite <money@magnoliaacvv.co.za>','021 - 948 6085'),('ACVV Huis Malan Jacobs ACVV Tehuis vir Bejaardes (PF063)','PF063','21','Done','18040,95','30.09.2024','','01.10.2024','Successful','hmjlaingsburg@gmail.com',''),('ACVV Malmesbury (PF064)','PF064','5','','11658,57','','100% update member info on RFW','','Successful','ACVV Malmesbury Dienssentrum Bestuurder <mbury.dienssentrum@acvv.org.za>',''),('ACVV Somerset Wes Huis Marie Louw (PF065)','PF065','22','Done','24471','27.09.2024','','07.10.2024','Successful','Jo-Ann Theron <fin.huismarielouw@acvv.org.za>',''),('ACVV Ceres Huis Maudie Kriel (PF066)','PF066','51','Done','55755','03.10.2024','RECEIVED LID INFO upload when SEP is open','04.10.2024','Successful','RIANA THEUNISSEN <maudie@lando.co.za>',''),('ACVV Middelburg Oos-Kaap (PF067)','PF067','5','Done','3317,83','25.09.2024','100% update member info on RFW','27.09.2024','Successful','yvonne@adsactive.com',''),('ACVV Kuruman Mimosahof (PF068)','PF068','21','Done','19196,7','25.09.2024','','27.09.2024','Successful','Finansies <mimosahof1@gmail.com>','082-495-5862'),('ACVV Mitchells Plain (PF069)','PF069','10','','19414,6','','','','Successful','accounts@acvvct.org.za',''),('ACVV Montagu (PF070)','PF070','5','Done','8874,49','16.09.2024','100% update member info on RFW','20.09.2024','Successful','ACVV Montagu <admin@acvvmontagu.co.za>','023-614-1490'),('ACVV Moorreesburg (PF071)','PF071','35','Done','35463,53','27.09.2024','100% update member info on RFW','07.10.2024','Successful','Huismoorrees Fin <huismoorreesfin@pcnetmail.co.za>','022-433-1477'),('ACVV Moreson ACVV Kinder- en Jeugsorgsentrum (PF072)','PF072','27','Done','47295,15','26.09.2024','','30.09.2024','Successful','Môreson Treasurer <moreson.admin@acvv.org.za>','044 874 4798'),('ACVV Mosselbaai (PF073)','PF073','123','Done','136371,15','26.09.2024','','30.09.2024','','Jan Venter <mosselbaaitesourier@acvv.org.za>',''),('ACVV Springbok Huis Namakwaland (PF074)','PF074','32','Done','26888,25','25.09.2024','100% update member info on RFW','30.09.2024','Successful','FINANSIES <finance@huisnamakwaland.co.za> ; andre@acvv.org.za',''),('ACVV Despatch Huis Najaar (PF075)','PF075','14','Done','11893,2','26.09.2024','','03.10.2024','Successful','accounts@huisnajaar.co.za',''),('ACVV Porterville Tak Huis Nerina (PF076)','PF076','32','Done','34259,61','16.09.2024','100% update member info on RFW','18.09.2024','Successful','Sunette Beck <fin.huisnerina@acvv.org.za>','022 931 2720'),('ACVV Dordrecht (PF077)','PF077','16','Done','12145,1','26.09.2024','100% update member info on RFW','07.10.2024','','Nerinahof Ouetehuis <nerinahof@gmail.com>',''),('ACVV Worcester (PF078)','PF078','50','Done','56611,91','01.10.2024','','03.10.2024','','finansies@nuwerus.co.za',''),('ACVV Paarl Vallei Oase Dienssentrum (PF079)','PF079','3','Done','3066,54','26.09.2024','100% update member info on RFW','30.09.2024','Successful','Finansies | ACVV Paarl Vallei  <info@acvv-pvallei.org.za>','021-871-1515'),('ACVV Kimberley Ons Huis (PF080)','PF080','25','Done','21343,88','30.09.2024','100% update member info on RFW','01.10.2024','Successful','frans@acvv-kimberley.co.za','053 842 1141'),('ACVV Ons Tuiste ACVV Dienstak (PF081)','PF081','53','Done','73418,85','27.09.2024','100% update member info on RFW','28.09.2024','Successful','Lizandra - Ons Tuiste <fin.ons-tuiste@acvv.org.za>',''),('ACVV Op die Kruin ACVV Dienstak (PF082)','PF082','9','Done','5228,4','19.09.2024','100% update member info on RFW','27.09.2024','Successful','OpDieKruin ACVV <acvvopdiekruin@gmail.com> ; Gerhard Engelbrecht <mrg8181@gmail.com>','053 631 3130'),('ACVV Upington Oranjehof Tehuis (PF083)','PF083','31','Done','41999,1','02.10.2024','100% update member info on RFW','04.10.2024','','Admin Oranjehof ACVV Tehuis vir Bejaardes <admin@acvvoranjehof.co.za>','054 331 2044 / 054 332 1986'),('ACVV Caledon (PF014)','PF014','10','Done','11100,15','23.09.2024','100% update member info on RFW','30.09.2024','Successful','Rocksand Kellerman <fin.acvvdagsorg@gmail.com> ; finans.heidehof@twk.co.za','(023) 316 1505'),('ACVV Oudtshoorn (PF085)','PF085','147','Done','145608,8','26.09.2024','RECEIVED LID INFO upload when SEP is open','27.09.2024','Successful','Finansies @ Odn ACVV <fin.oudtshoorn@acvv.org.za>','044-272-2211'),('ACVV Paarl (PF086)','PF086','3','Done','6744,9','23.09.2024','100% update member info on RFW','25.09.2024','Successful','ACVV Paarl Tak <acvvpaarl@gmail.com>','021 872-2738'),('ACVV Noorder-Paal (PF087)','PF087','3','Done','8632,98','23.09.2024','100% update member info on RFW','27.09.2024','Successful','admin@acvvnp.org.za',''),('ACVV Paarl Vallei (PF088)','PF088','5','Done','9879,81','26.09.2024','100% update member info on RFW','30.09.2024','Successful','Finansies | ACVV Paarl Vallei  <info@acvv-pvallei.org.za>','021-871-1515'),('ACVV Newton Park PE (PF089)','PF089','2','Done','4308,78','01.10.2024','100% update member info on RFW','03.10.2024','Successful','From','Subject'),('ACVV PE Noord (PF090)','PF090','4','Done','7381,52','01.10.2024','100% update member info on RFW','','Successful','Johannes Petrus Beukman','Fwd: Pension Fund Sep 2024'),('ACVV Port Elizabeth Suid (PF092)','PF092','6','Done','7206,36','03.10.2024','100% update member info on RFW','05.10.2024','Successful','ADMIN - ACVV POPLARLAAN <admin@poplarlaan.acvv.co.za> ; Mary-Ann Coetzer <book@pesuid.acvv.co.za>',''),('ACVV Port Elizabeth Wes (PF093)','PF093','11','Done','23725,85','16.09.2024','100% update member info on RFW','23.09.2024','Successful','Accounts <accounts.pewes@lantic.net>','041 360 2106'),('ACVV Piketberg (PF094)','PF094','4','Done','9074,78','23.09.2024','100% update member info on RFW','30.09.2024','Successful','Elmarie van Rooyen <fin.piketberg@acvv.org.za>',''),('ACVV St Helenabaai (PF095)','PF095','16','Done','17151,19','25.09.2024','100% update member info on RFW','26.09.2024','Successful','aletta@visagieboerdery.com',''),('ACVV Poplarlaan PE (PF096)','PF096','2','Done','2400,68','01.10.2024','100% update member info on RFW','07.10.2024','Successful','ADMIN - ACVV POPLARLAAN <admin@poplarlaan.acvv.co.za>','060 810 6260 '),('ACVV Porterville Tak (PF097)','PF097','2','Done','3916,16','20.09.2024','100% update member info on RFW','25.09.2024','Successful','Sunette Beck <fin.huisnerina@acvv.org.za>','022 931 2720'),('ACVV Postmasburg (PF098)','PF098','1','Done','1271,38','25.09.2024','100% update member info on RFW','30.09.2024','Successful','ACVV Postmasburg <pmgacvv@gmail.com>','053 313 2164'),('ACVV Prieska (PF099)','PF099','4','','5480,11','','100% update member info on RFW','','','fin.prieska@acvv.org.za',''),('ACVV Caledon Protea Dienssentrum (PF100)','PF100','1','Done','672,58','26.09.2024','100% update member info on RFW','30.09.2024','Successful','finans.heidehof@twk.co.za','028 214 1755'),('ACVV Riebeek Kasteel (PF101)','PF101','9','Done','17476,06','16.09.2024','100% update member info on RFW','27.09.2024','Successful','ACVV Riebeek Kasteel Manager <manager@acvvrk.org>','(022) 448-1715'),('ACVV Riversdal (PF102)','PF102','11','Done','17832,41','25.09.2024','100% update member info on RFW','30.09.2024','Successful','info@shovelprojects.co.za','028-713-1378'),('ACVV Robertson Huis Le Roux (PF103)','PF103','22','Done','25557,56','23.09.2024','100% update member info on RFW','27.09.2024','Successful','ACVV Huis le Roux <fin.huisleroux@acvv.org.za>','(023) 626-3163'),('ACVV Robertson (PF104)','PF104','10','Done','13308,6','16.09.2024','100% update member info on RFW','23.09.2024','Successful','fin2 <fin2@acvvrobertson.org.za>','023-626-3097'),('ACVV Rusoord Tehuis vir Oues van Dae Paarl (PF105)','PF105','35','Done','44169,65','26.09.2024','100% update member info on RFW','04.10.2024','Successful','finansies@rusoordtehuis.co.za ; Lucinda Scholtz <bestuurder@rusoordtehuis.co.za>',''),('ACVV Clanwilliam (PF106)','PF106','28','Done','29596,8','26.09.2024','RECEIVED LID INFO upload when SEP is open','04.10.2024','Successful','Admin <admin@acvvsederhof.org.za>',''),('ACVV Somerset Oos Huis Silwerjare (PF107)','PF107','12','Done','8554,92','27.09.2024','100% update member info on RFW','04.10.2024','Successful','Rika Scheun <fin.silwerjare@acvv.org.za>','04224 32107'),('ACVV Wellington Tak Silwerkruin (PF108)','PF108','62','Done','66027,42','19.09.2024','100% update member info on RFW','23.09.2024','','Johanitia Coetzee <finans1@silwerkruin.com>','021-873-1040'),('ACVV Elizabeth Roos Tehuis Dienstak (PF110)','PF110','11','Done','14805,3','25.09.2024','100% update member info on RFW','30.09.2024','Successful','Accounts Elizabeth Roos <bookkeeper.elizabethroos@gmail.com>','021-462-1638'),('ACVV Skiereiland Beheerkomitee van die ACVV Dienstak (PF111)','PF111','12','Done','28050,84','25.09.2024','100% update member info on RFW','27.09.2024','','Albida McMillan <accounts@acvvpen.co.za>',''),('ACVV Strand Soeterus Tehuis (PF112)','PF112','23','Done','23812,5','25.09.2024','100% update member info on RFW','27.09.2024','Successful','Amanda Klem <finansies@soeterus.com>','(021) 853 7423'),('ACVV Lambersbaai Somerkoelte Tehuis (PF113)','PF113','37','','31030,71','','100% update member info on RFW','','Successful','somerkoelte.finansies@gmail.com',''),('ACVV Somerset Wes (PF115)','PF115','5','Done','12861,2','20.09.2024','100% update member info on RFW','30.09.2024','Successful','ACVV SWES <acvvswes@telkomsa.net>','021-852-2103'),('ACVV De Aar Sonder Sorge Tehuis (PF117)','PF117','25','Done','21839,81','23.09.2004','100% update member info on RFW','06.10.2024','Successful','Riana Raath <truteriana@gmail.com>',''),('ACVV Calvinia (PF118)','PF118','35','Done','32498,85','20.09.2024','RECEIVED LID INFO upload when SEP is open','28.09.2024','Successful','Sorgvliet Tehuis <sorgvliet@hantam.co.za>','027-341-1223'),('ACVV Strand Speelkasteel (PF120)','PF120','17','Done','19876,5','01.10.2024','100% update member info on RFW','03.10.2024','Successful','Speelkasteel Strand boekhouer <speelkasteelstrandboekhouer@acvv.org.za> ; speelkasteelstrand@acvv.org.za',''),('ACVV Douglas (PF121)','PF121','31','Done','34599,7','23.09.2024','100% update member info on RFW','27.09.2024','Successful','ACVV Spes Bona <fin.spesbona@acvv.org.za>','053 298 1035'),('ACVV Stellenbosch (PF123)','PF123','20','Done','33941,18','25.09.2024','100% update member info on RFW','30.09.2024','Successful','fin.stellenbosch@acvv.org.za','021 887 6959'),('ACVV Worcester Stilwaters Dienssentrum (PF124)','PF124','3','Done','3894','27.09.2024','100% update member info on RFW','28.09.2024','Successful','Brian Baard <stilwatersfin@acvvcw.co.za>','(023) 342 0634'),('ACVV Die Afrikaanse Christelike Vrouevereniging Strand (PF125)','PF125','12','Done','25858,65','30.09.2024','100% update member info on RFW','04.10.2024','Successful','Jacqueline Dippenaar <strandadmin@acvv.org.za>','(021) 854 7215'),('ACVV Bredasdorp Suideroord Tehuis (PF126)','PF126','92','Done','111220,95','27.09.2024','RECEIVED LID INFO upload when SEP is open','30.09.2024','Successful','Corrali Groenewald <rekeninge1@suideroord.co.za>','028 424 1080 '),('ACVV Swellendam (PF127)','PF127','3','Done','6849,75','16.09.2024','100% update member info on RFW','25.09.2024','Successful','Ronel Groenewald <fin.swellendam@acvv.org.za>',''),('ACVV Middelburg Oos Kaap Huis Karee (PF130)','PF130','10','Done','12134,77','25.09.2024','100% update member info on RFW','30.09.2024','Successful','huiskaree@gmail.com','049-842-2151'),('ACVV Upington (PF131)','PF131','6','','10059,64','','100% update member info on RFW','','','acvv@isat.co.za',''),('ACVV Utopia ACVV Tehuis vir Bejaardes Dienstak (PF132)','PF132','10','Done','20385,96','16.09.2024','100% update member info on RFW','27.09.2024','Successful','anneen@utopiastb.co.za , Annelie van Eeden <annelie@ffas.co.za> , admin@utopiastb.co.za , Lila Botha <lilabotha1602@gmail.com>',''),('ACVV Kirkwood Valleihof Tehuis (PF133)','PF133','28','Done','28634,1','25.09.2024','100% update member info on RFW','26.09.2024',' ','fin.valleihof@acvv.org.za','042 2300 393'),('ACVV Graaff-Reinet Huis van de Graaff Tehuis (PF134)','PF134','25','Done','18160,94','25.09.2024','','04.10.2024','','ACVV Graaff-Reinet <acvvgraaffreinet@telkomsa.net>','049-892-3229'),('ACVV Huis Van Niekerk Benadehof ACVV Dienssentrum Dienstak (PF135)','PF135','45','Done','78080,85','23.09.2024','','26.09.2024','Successful','Charmaine van den Heuvel <finansies@vnbh.org.za>','021 853 1040/1'),('ACVV Huis Vergenoegd Dienstak Diens en Dag (Paarl) (PF136)','PF136','3','Done','13568,99','01.10.2024','100% update member info on RFW','03.10.2024','Successful','Morné Swanepoel <hvg1@lando.co.za>',''),('ACVV Huis Vergenoegd Dienstak Siekeboeg (Paarl) (PF137)','PF137','72','Done','100099,47','01.10.2024','RECEIVED LID INFO upload when SEP is open','02.10.2024','Successful','Morné Swanepoel <hvg1@lando.co.za>',''),('ACVV Huis Vergenoegd Dienstak Woonstelle (Paarl) (PF138)','PF138','33','Done','42133,42','01.10.2024','','03.10.2024','Successful','Morné Swanepoel <hvg1@lando.co.za>',''),('ACVV Wellington Tak (PF139)','PF139','2','Done','5424','17.09.2024','100% update member info on RFW','05.10.2024','Successful','Steven von Schlicht <well.admin@acvv.org.za>','021-873-2204'),('ACVV Wellington Tak Fyngoud Dienssentrum (PF140)','PF140','2','Done','3660,66','04.10.2024','100% update member info on RFW','05.10.2024','Successful','Adri van Zyl <acvvfyngoud@acvv.org.za>',''),('ACVV Paarl Vallei Wielie Walie Creche (PF141)','PF141','6','Done','5558,86','26.09.2024','100% update member info on RFW','30.09.2024','Successful','Finansies | ACVV Paarl Vallei  <info@acvv-pvallei.org.za>','021-871-1515'),('ACVV Weskusnessie Dienstak (PF142)','PF142','23','Done','23393,5','03.10.2024','100% update member info on RFW','04.10.2024','Successful','Lizl Ryan <lizlryan@gmail.com>',''),('ACVV Danielskuil (PF143)','PF143','5','Done','6700,11','30.09.2024','100% update member info on RFW','04.10.2024','Successful','acvvdanielskuil <acvvdanielskuil@gmail.com>',''),('ACVV Victoria Wes Wiekie Wessie Creche (PF144)','PF144','1','Done','712,39','28.09.2024','','01.10.2024','','Christina Steenkamp <vicwesacvv2@gmail.com>;Denise Els <elsdenise3@gmail.com>',''),('ACVV Worcester (PF145)','PF145','4','Done','7765,8','27.09.2024','100% update member info on RFW','28.09.2024','Successful','Brian Baard <stilwatersfin@acvvcw.co.za>','(023) 342 0634'),('ACVV Ysterplaat Dienstak van die ACVV (PF146)','PF146','29','Done','31781,75','25.09.2024','100% update member info on RFW','27.09.2024','Successful','Finance Ria Abel Home <finances@homeriaabel.co.za>','021-511-8119'),('ACVV Zonnebloem ACVV Dienstak (PF147)','PF147','41','Done','39234,15','30.09.2024','RECEIVED LID INFO upload when SEP is open','01.10.2024','Successful','Moira Marincowitz <zonnebloemfinansies@acvv.org.za>',''),('ACVV Strand Dienssentrum vir Seniors (PF148)','PF148','4','Done','12411,62','27.09.2024','100% update member info on RFW','01.10.2024','Successful','Domé Sonnekus <admin@strandsds.co.za> ; info@strandsds.co.za',''),('ACVV Grabouw Appelkontrei Dienssentrum (PF149)','PF149','1','Done','1518','17.09.2024','100% update member info on RFW','30.09.2024','Successful','fin.huisgroenland@acvv.org.za ; manager@huisgroenland.co.za','021 859 4209'),('ACVV Reivilo Dienssentrum (PF150)','PF150','4','Done','1200','27.09.2024','100% update member info on RFW','01.10.2024','','Leone Jansen van vuuren <leone.jansenvanvuuren@gmail.com> ; doretteweideman@gmail.com',''),('ACVV Elandsbaai (PF151)','PF151','2','Done','2491,6','20.09.2024','100% update member info on RFW','25.09.2024','Successful','Marlise Smit <marlise@smitrek.co.za>','060-995-7365'),('ACVV Colesberg Old Age Home (PF155)','PF155','7','Done','6672,32','23.09.2024','100% update member info on RFW','27.09.2024','Successful','Huis Kiepersol Huis Kiepersol <huiskiepersol1@gmail.com>',''),('ACVV Triomf Child Care Centre (PF156)','PF156','8','Done','8321','26.09.2024','100% update member info on RFW','07.10.2024','Successful','Sharon Hay <sharon@thebarn.co.za>',''),('ACVV Barrydale (PF157)','PF157','1','Done','1170,9','25.09.2024','100% update member info on RFW','27.09.2024','Successful','Lucinda Van der Berg <fin.barrydale@acvv.org.za>','028 572 1995 | Cell: 0711279004'),('ACVV Malmesbury Dienssentrum (PF161)','PF161','4','','4771,86','','100% update member info on RFW','','Successful','malmesbury.tak@acvv.org.za',''),('ACVV Somerset Wes Tinktinkie (PF163)','PF163','5','Done','4596,38','20.09.2024','100% update member info on RFW','30.09.2024','Successful','ACVV SWES <acvvswes@telkomsa.net>','021-852-2103'),('ACVV Despatch (PF165)','PF165','2','Done','2969,96','04.10.2024','100% update member info on RFW','07.10.2024','Successful','Wilma Laubscher <socialworker@acvvdespatch.co.za>',''),('ACVV Kuruman Heuwelsig (PF166)','PF166','4','Done','5123,94','20.09.2024','100% update member info on RFW','25.09.2024','Successful','fin.heuwelsig <fin.heuwelsig@acvv.org.za>','053-712-0447'),('ACVV Port Elizabeth Sentraal Khayalethu Jeugsentrum (PF168)','PF168','11','Done','21507,75','20.09.2024','100% update member info on RFW','30.09.2024','Successful','Amelia Otto <bookkeeper@khayalethu.org.za> ; Marietjie <khaya@khayalethu.org.za>','041 484 5667'),('ACVV Piketberg Trippe Trappe (PF169)','PF169','5','Done','4585,66','23.09.2024','100% update member info on RFW','30.09.2024','Successful','Elmarie van Rooyen <fin.piketberg@acvv.org.za>',''),('ACVV Robertson Jakaranda Dienssentrum (PF171)','PF171','3','Done','4008','16.09.2024','100% update member info on RFW','23.09.2024','','fin2 <fin2@acvvrobertson.org.za>','023-626-3097'),('ACVV Worcester Bollieland Creche (PF172)','PF172','11','Done','10606,12','02.10.2024','100% update member info on RFW','03.10.2024','Successful','ACVV Bollieland Creche <fin.bollieland@acvv.org.za>','023-342-0760'),('ACVV Moorreesburg Kleuterland (PF173)','PF173','10','Done','10142,89','27.09.2024','100% update member info on RFW','07.10.2024','Successful','Huismoorrees Fin <huismoorreesfin@pcnetmail.co.za>','022-433-1477'),('ACVV Moorreesburg (PF174)','PF174','5','Done','8936,7','27.09.2024','100% update member info on RFW','07.10.2024','Successful','Huismoorrees Fin <huismoorreesfin@pcnetmail.co.za>','022-433-1477'),('ACVV Dienssentrum Moorreesburg (PF175)','PF175','2','Done','2007,21','27.09.2024','100% update member info on RFW','07.10.2024','Successful','Huismoorrees Fin <huismoorreesfin@pcnetmail.co.za>','022-433-1477'),('ACVV Moorreesburg Heuwelsig (PF176)','PF176','1','Done','784,89','27.09.2004','100% update member info on RFW','07.10.2024','Successful','Huismoorrees Fin <huismoorreesfin@pcnetmail.co.za>','022-433-1477'),('ACVV Dysselsdorp Swartberg Dienssentrum (PF181)','PF181','2','Done','1296,08','30.09.2024','100% update member info on RFW','02.10.2024','','acvvfinansies@scwireless.co.za','044 251 6721 / 062 405 4918'),('ACVV Dysselsdorp Siembamba Creche (PF182)','PF182','5','Done','2880','30.09.2024','100% update member info on RFW','02.10.2024','','acvvfinansies@scwireless.co.za','044 251 6721 / 062 405 4918'),('ACVV Yzerfontein','PF183','1','Done','1525,71','20.09.2024','100% update member info on RFW','25.09.2024','','acvvyzerfontein@gmail.com','022 451 2494'),('ACVV Dysselsdorp Shelter (PF184)','PF184','3','Done','2360,12','30.09.2024','100% update member info on RFW','02.10.2024','','acvvfinansies@scwireless.co.za','044 251 6721 / 062 405 4918'),('ACVV Riebeek Wes Humanitas (PF050)= PF185 ','PF185','2','Done','1358,6','02.10.2024','100% update member info on RFW','03.10.2024','Successful','fin.riebeekwes@acvv.org.za','022-461 2721'),('ACVV Port Elizabeth Sentraal (PF091)PF186)','PF186','1','Done','1845','03.10.2024','100% update member info on RFW','05.10.2024','Successful','elko@iafrica.com',''),('ACVV Marinerylaan (PF180)','PF180','1','NEW FUND 01.08.2024','','','nuwe lid vanaf 1.08.2024 wag op christel -tak ni aktief op rfw nie','','','johanbeukman.irispark@gmail.com','');
/*!40000 ALTER TABLE `global acvv` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-12-17 12:01:46
