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
-- Current Database: `acvv_app`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `acvv_app` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `acvv_app`;

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
INSERT INTO `acvv_outlook_token` VALUES (1,'acvv@futurasa.co.za','eyJ0eXAiOiJKV1QiLCJub25jZSI6IjhtYS1WcmNxV2w1MVNsdGs3U0VmYXg2eC1pTllrNDNxRWN4SXNqMzd3ZVkiLCJhbGciOiJSUzI1NiIsIng1dCI6IndoMDZzRWt6TEhKNXNOTmFVeVJZMl82TzhLMCIsImtpZCI6IndoMDZzRWt6TEhKNXNOTmFVeVJZMl82TzhLMCJ9.eyJhdWQiOiJodHRwczovL2dyYXBoLm1pY3Jvc29mdC5jb20iLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC83YmNmYzA4MC1lMWYxLTRmOTktYjRlZC1lMWE5NmVkYTg5Y2UvIiwiaWF0IjoxNzgwNjAwMTA5LCJuYmYiOjE3ODA2MDAxMDksImV4cCI6MTc4MDYwNDAwOSwiYWNycyI6WyJwZmRyIl0sImFpbyI6ImsyRmdZT0M2cnBvd3BVSjd3NWFpQ2VwVEdKd3pXUGoyN0QyMXB6Nnk5ZTJWZk4wSURUOEEiLCJhcHBfZGlzcGxheW5hbWUiOiJGdXR1cmEtQXBwIiwiYXBwaWQiOiI5ZjgyZTU3ZC00NWE0LTRiNjYtYWIyOS04YTliMzgxYTA4MmEiLCJhcHBpZGFjciI6IjEiLCJpZHAiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC83YmNmYzA4MC1lMWYxLTRmOTktYjRlZC1lMWE5NmVkYTg5Y2UvIiwiaWR0eXAiOiJhcHAiLCJvaWQiOiI0MTc2NDgyNy0yZGJlLTRiMTYtYWJhNi0xZDIwMDYxYjU5MWYiLCJyaCI6IjEuQVNBQWdNRFBlX0hobVUtMDdlR3BidHFKemdNQUFBQUFBQUFBd0FBQUFBQUFBQUFBQUFBZ0FBLiIsInJvbGVzIjpbIk1haWwuUmVhZCIsIk1haWwuU2VuZCJdLCJzdWIiOiI0MTc2NDgyNy0yZGJlLTRiMTYtYWJhNi0xZDIwMDYxYjU5MWYiLCJ0ZW5hbnRfcmVnaW9uX3Njb3BlIjoiQUYiLCJ0aWQiOiI3YmNmYzA4MC1lMWYxLTRmOTktYjRlZC1lMWE5NmVkYTg5Y2UiLCJ1dGkiOiJ5aFdvaV9XS3NFdWVXcXItekZnZUFBIiwidmVyIjoiMS4wIiwid2lkcyI6WyIwOTk3YTFkMC0wZDFkLTRhY2ItYjQwOC1kNWNhNzMxMjFlOTAiXSwieG1zX2FjZCI6MTc2NDE2MDkyNiwieG1zX2FjdF9mY3QiOiIzIDkiLCJ4bXNfZnRkIjoiRmkxLWhjQU85ZW9QakMzY252cVlnT25FSDFpRFF6TzBPSGloYjdnUGVuOEJabkpoYm1ObFl5MWtjMjF6IiwieG1zX2lkcmVsIjoiMTQgNyIsInhtc19wZnRleHAiOjE3ODA2OTA0MDksInhtc19yZCI6IjAuNDJMbFlCSmlWQkFTNFdBWEV2aFM4X2Ria2R4T3g1bF9jajdPVU42bUp5VEN3U2trOExZaE9TeWtwOWw5dWdMRDY3S3lXbDhoRVE0T0lRRm1CZ2c0QUtXRlJEaTRoUVJlX0p4eWNfZUZFdjJ0cF9qbEx6R2R6Z2NBIiwieG1zX3N1Yl9mY3QiOiIzIDkiLCJ4bXNfdGNkdCI6MTQ5OTcxMjQyMCwieG1zX3RudF9mY3QiOiIzIDYifQ.l8Je0Bzk52xyvUDgvT7X3zS04BxPeybPpFL5uORG3nHiskHTn5d9Iqu9WoETAyAeFRyr8nsl3sur8lTAvKKTYHhqufejozPHZe5igp1z5k_uEsaK3hpVJs0Ubc64livpGnLozBc2ja4Eo_hXtAS00yb_N2SnQpDTCIyGDXPAHVvjI1I24W59zWDRo7ZJSvyWgOy9Es1MjB0MGxUmxkftAi3qjcObxG5pj6BWSQTacty7ivoEM48ZgkYdWYBvKYOnBDszwEp3rmOJmfMTDQ_2cMEYY_DLCBkJfu1EIf7KRNzRzeoTYiaG1NBHWDHFGeJME_csCVkjPjtNVhj0EDVjfg',NULL,3599,'2026-06-04 19:13:29.911683');
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
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user`
--

LOCK TABLES `auth_user` WRITE;
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
INSERT INTO `auth_user` VALUES (1,'pbkdf2_sha256$1000000$0zg9UjZB2zeXSXInM9C3Md$igTZw8J2jh3znUITqGVLWa7Rnm0XOjrpqtc21GO/uQs=','2026-06-04 18:12:56.427789',1,'omega','','','',1,1,'2025-09-19 11:24:27.343696'),(2,'pbkdf2_sha256$1000000$dmFBjFd3XWtYQDePDKE1qQ$VbHMeUILJFaR9aZ7eTTIm3qpJmz2ixVbAlv+hbMLrNA=','2025-12-11 09:31:18.620642',0,'testuser','','','test@example.com',0,1,'2025-12-11 08:24:58.760332'),(3,'pbkdf2_sha256$1000000$A6jOIWZeJPKi5HOwLb1Lxv$bjhJFbJALlW79g9YGYS9xhIDlHvbo0DsAGglo9TlvRY=','2026-05-15 19:38:52.552967',0,'testuser1','','','',0,1,'2025-12-17 09:59:07.678369'),(4,'pbkdf2_sha256$1000000$7SPlHWZzImqF6bgXpBsmQf$JAfm9A/lxtXqSjfM/oU/o8yeZ264hgAqzS+VzhUOvCI=',NULL,0,'testuser2','','','',0,1,'2025-12-17 09:59:08.012316'),(5,'pbkdf2_sha256$1000000$VuhW8ZRFtGZyuKEXYsom32$6DFdB0pUijLFEZ3xbOBy/ROb4tKl0Z+4MDPulqVzPhM=',NULL,0,'testuser3','','','',0,1,'2025-12-17 09:59:08.337488'),(6,'pbkdf2_sha256$1000000$OBszZ7dhhdPgkL7xuTC2h3$dw2k2ERlcYoHZRZvUNsRrizQGT7XAI+FiHpdafrNK1Q=',NULL,0,'testuser4','','','',0,1,'2025-12-17 09:59:08.662876'),(7,'pbkdf2_sha256$1000000$Ouds85Q9NehDgXbOnw0kIc$7Wyyfw6SDjlTx4hwG60i2ofqUyT/29T4qAJuL1GByGw=','2026-05-19 18:42:39.381683',1,'Jesica','','','',1,1,'2026-04-14 19:29:11.811692'),(8,'pbkdf2_sha256$1000000$n6oDRWLSD8PowSqmorgKtN$wdLaMBde339ZwFYvcRIjEM+t/W9b4bMAzbLALEghX6E=','2026-04-14 19:30:20.368777',0,'Timothy','','','',1,1,'2026-04-14 19:29:12.133379'),(9,'pbkdf2_sha256$1000000$hjZPARi4gv51eCxvIBYA9o$NKLD5qQN6prGU15IjYUZ/s9xIg/2S8pnsGAHBiyxdwg=',NULL,0,'Chantal','','','',1,1,'2026-04-14 19:29:12.453288'),(10,'pbkdf2_sha256$1000000$BUKHpVToswWrW6okJyS2QO$geRacsmm/zHC5jydG12P6V3cSbSQT8OA/e3k4Fqk1O4=','2026-05-06 20:03:14.544242',1,'Samantha','','','',1,1,'2026-04-14 19:29:12.846685'),(11,'pbkdf2_sha256$1000000$SxnUeuZQ7ifmz2P0JnHtp7$CgXJuhpQsmAW9NMvCAL5DJ5bgEvojz2vk5Q/5DQlM/w=',NULL,1,'Lorraine','','','',1,1,'2026-04-14 19:29:13.290373');
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
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `client_notes`
--

LOCK TABLES `client_notes` WRITE;
/*!40000 ALTER TABLE `client_notes` DISABLE KEYS */;
INSERT INTO `client_notes` VALUES (1,'ACVV Aberdeen (PF001)','2026-06-04 19:16:11','omega','Email delegated to omega','Email Delegation','General','');
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `delegation_note`
--

LOCK TABLES `delegation_note` WRITE;
/*!40000 ALTER TABLE `delegation_note` DISABLE KEYS */;
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
INSERT INTO `django_session` VALUES ('018qwmxfyz2tadifujxw32jbr2xdq22e','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1v0c12:DjtpoiIKLphnUVFzKC0tiW1E9hkxCUoRrWB5H89vcgk','2025-10-06 08:35:20.587529'),('2d9fjhdj825wf38ekhrvjb409r0e732c','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1v0fqL:2FyIHs5Le40E47vCzkPYoEvmn8hBjE5zPbrgXv8IK3o','2025-10-06 12:40:33.162859'),('2fuwzmx8ybi61s38ceor8j6e517410cc','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1wTPRR:vJ3vmMeM-SBRiGu44Ildoaz6_Vdb-iKQTTs-Gj84eNY','2026-06-13 19:33:53.360971'),('2kb9wbxsis1qm9ekdf68hhbgmxjyvcgy','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vOcjg:vAkru7Z6gEo4aQ8h3D2c6aYCu09qKSw9fbhRfAmjr8Q','2025-12-11 14:12:40.542000'),('2ryh8ntcvu5wa5oqbtzgnlhyj54i2fwr','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1v1ibn:G8ikhiVtjwxWTg61pMWtrF_NZF1qcMChCXARzXSm_5Y','2025-10-09 09:49:51.511498'),('2u1xapmm8ky5d50zvhb208o5dmxsq4ti','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vWDNc:1L3gOxyD2eI-JPurhrcFzLLkC7Yc5LE2Me5QQeuLYOU','2026-01-01 12:45:16.693716'),('32mafyj110632k3okrl2qroai0nvka9b','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1v4FNz:cvj2_s4RMSAnZ6Qh_T8_0LlzZpjBc8Uwg_UoS0pnYcI','2025-10-16 09:14:03.408365'),('33arhbzgc6y6v9eezfv5s221zpcc9efp','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1wKKZZ:jqUHIkDmXqLHqjQ3l0WBtke6HUgsKwIkpIG04onWWCA','2026-05-19 18:32:45.838953'),('4pvaa7i9r6myclyrfr96thrp34fcnn0m','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1viAxg:vYO650t5TR-6LMyCux4sgE3XF0xozWUsFn-6rtMC-c0','2026-02-03 12:35:56.639035'),('4roqytzc3grp8d6i5afxsj5si1fgczlw','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vqpUQ:yCVhr3BdR406erluNKYAeA-c48dh9CahC5c7TDizjMw','2026-02-27 09:29:30.152211'),('4xbr8ql7tz59l7ai1as2p4vg03zltw5b','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1v0gmE:HwnFn3kixVObykipbhUzbVUeOSIFaZt4DdcyuuY4rmU','2025-10-06 13:40:22.320585'),('5kqqgt4dffj3ghdrdz3qbwz8k6zn67on','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vkg2v:O6XmEUoQSH3HO52IA8xVSgJX-T32ubKnQ1ph6M-JTIM','2026-02-10 10:11:41.200353'),('7fjpfeffsdxsc1s2dzoqsufzzdwvvdq7','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vSxQ8:CtS9xsPBwh9Txo9AaIziVwItG5Kgp2sEa2vR0bvrNMA','2025-12-23 13:06:24.768193'),('7xrd4xrip44lo61gguspfkxd7dq3x3h0','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1wCMBD:Ka9cdNywgRbP5WbFMax_ysRQF6ZPd3Mo8BLKROd5r3k','2026-04-27 18:38:39.947333'),('81k5qkci9cl57c2r5tpdqffvzlnwje8m','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1w9hUv:z8B7anfSQ1vuDvu92xBJFcTU5Nmclv_jV1MVRr4zZWA','2026-04-20 10:48:01.303895'),('81xp600agcijlprgzlnyi4vujnd18mbu','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vlLOP:1Qzs6LlEUPt3elDZAn8ew20_IAjnS9fn5J1uwP6wXPw','2026-02-12 06:20:37.013848'),('afd9eo10ao41mlqogjkz9lo3plhtt3ja','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vgHZD:bKAK8l1fdkjA6vIj1QHLsSaUYRoPLoavHW12hzEm8wo','2026-01-29 07:14:51.628953'),('ah29ugr3rjzbapna304dg56sizd9x0yv','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vfeTH:cuEpl-23cQbV70KjgWQXpGfJRK3IOqH1jVC4FOUkKYc','2026-01-27 13:30:07.907517'),('apeiyv097esg2dmaajdgqbkia26ic0nt','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1v0aqe:FpyzmyU0o9IoVUrFsxZBCooF0oyp2kyt0OCNkL6zRB0','2025-10-06 07:20:32.380066'),('c74rdv9qapqp4iqzsp4jv6mljc7f8x3i','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1wKib1:kd7sqFf-i_-fAoJ_M2J1u8RuwCKYIpf-Kocxd0yTPCk','2026-05-20 20:11:51.139247'),('d8w8rdn5m2utewus23cre3ipzrc0nirz','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1wKKkO:V42WDUIh3iXlsUA1TSjkICjMXun8Wr1Y5pm7U5HYwVA','2026-05-19 18:43:56.588654'),('dq5b08w0ntrcvn7y7470gznp6l0tzixw','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1v0xrk:Bqo8CuLED0d_ZlDP436cSojDNkm5SlbpJvhzIksBaXo','2025-10-07 07:55:12.318694'),('fpbvp5qlrfs8ygbpyal9ly6x07a4hmp2','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1v0zVK:OSishOOoLAFS_aNFM1okDciqibEqZvicCBvvjHBoo5M','2025-10-07 09:40:10.535461'),('frllo05273a4lc1dscr1t5kkd92lutv2','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1wEtO9:D7vrok10a2WKz0CNMfYKeSUFC6LlzYTdM6f6iiREBpY','2026-05-04 18:30:29.796305'),('fuiv5umv7s62884lfvus0v69md7d8rzr','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1wD531:M3etu1droGGtcUqc8NPFdwp2FiqX9vKe-RyQLMYaPm4','2026-04-29 18:33:11.570850'),('fyrfrtm2njlh1w4tk7vupm7rbwgch35c','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vvYtL:ocOlCZG_d4fZBLmRNwfzks3HwRUPdkM8lx4juEW5KYI','2026-03-12 10:46:47.511694'),('h41n0pdtuuijetfc3z9ap6ys7txxdubm','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1wABRb:piDKd_LewXnaldS1UASUCwhz8HH5jfXkLaN4wM4ZUZE','2026-04-21 18:46:35.362391'),('h7i56ttmxmeq7a1yzj5t3hbn7zhdglyz','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1w7cQ3:LJuOUqF_X2IDnejm64VL1TgV_42tWB64QrFfYvYt3I8','2026-04-14 16:58:23.674323'),('haq5xcti9ails7szue4s2zyusztcoxe8','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1wVCYq:2JVK38GHZIH7gHz2SM4GFvWZzTMNEdWnAbz9oX44qd0','2026-06-18 18:12:56.444145'),('hqnq9e86cv9vxbyckjh3jhgxxcdcl03e','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1wLmb5:f7l5j3P2uONX17ydEx0jBDerFvfyVGR_gOEPLOYn_JM','2026-05-23 18:40:19.114052'),('hqvhhrwpbuw3dw152yp518naoa2zlij7','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vTPJ5:1I40ajLXJHOS2ukCbNdaAMyJ2kto5hloI_UCX8mQDXE','2025-12-24 18:52:59.836797'),('jxejadl4oazajfkz7btaabahfiszd31w','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vlNj3:sa6CEXi_ghoDub5Eb2Yi3A7BgRS9ORM7W25qtrsEd1E','2026-02-12 08:50:05.519516'),('kiz2zhkcusp1k65kv6rsode2msfaumu6','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1v0dUE:doUpjmxx1WXqkkxLr8nv9eZgIYZbhmZI7blriWLNCjk','2025-10-06 10:09:34.546298'),('l8dqjfgttycejc9ouxaux74au86vs2ho','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1w9ouj:GH-Q45kpaaVpDBoaXxOaCy9xxepp1yJvdvLTggSUbgM','2026-04-20 18:43:09.705837'),('ljfijttts8gmmtaurzzxevl7i3tenuxv','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1wACH7:PvOtIKLE7oMGOX7vyJJ8zDKXtz0RUTUp6Kis-OahVgQ','2026-04-21 19:39:49.990518'),('lycdf2q5duoakuhxghcc2hd7yn8x3ue9','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1v0gSJ:SRpDIBo029DoNWsKe-Q2W8nPFpKX_GpiA_1G6VhqT6U','2025-10-06 13:19:47.032976'),('may4x2dcrsxxgrtj2dewpl497ll4bbo9','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1w1rql:xUEUV6B5iFCwH0OyjrZfCYgzq6lk3lFPGFykYb0ek5k','2026-03-29 20:14:11.600935'),('mvm3rpfyyrruc47nkjr0goxe6fsj3yuk','.eJxVjEEOwiAURO_C2hCwtL-4dO8ZyB_4laqBpLQr491Nky50O--9eavA25rD1mQJc1IXZY06_Y7g-JSyk_Tgcq861rIuM_Su6IM2fatJXtfD_TvI3PJeO7BPgxUGj3YSk4h7CwzoYajrDMN5R5jsSF4o9jI6a84wbiIQkvp8ASuNOLE:1wDpVE:L3LeJoPW3Oq4RYjEgVH_0yeEsFPFefhCJA37GvzOjQk','2026-05-01 20:09:24.049967'),('nia3e6x0a6o2btly5md8vblsmgkolkwm','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1viYIf:fEmhQuwNFGMPDswk7M8x-qghsKctPIDvWYwW3A9Bctg','2026-02-04 13:31:09.782201'),('pyap4iqiyseo70dnoxfm9hygswbe7sfh','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vU0Ji:wMJ49uYEZOf0_kWjkIY_ZAeju61yVJC5iest0AG4VSE','2025-12-26 10:24:06.124490'),('qg754gwk3ajw5t2sbhu61mgddsimzbvp','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1w1qVQ:ZAD_gDzf7cbEMgi8JdCylVGVpPjVb2SWFjyRwOX3TzU','2026-03-29 18:48:04.162242'),('qqvjep0fjbq4x5qtvnq1mnp3fuq6m5qk','.eJxVjEEOwiAQRe_C2hAYHKAu3fcMZBhAqoYmpV0Z765NutDtf-_9lwi0rTVsPS9hSuIijDj9bpH4kdsO0p3abZY8t3WZotwVedAuxznl5_Vw_w4q9fqtWfkEqAGMimish8ExaYoaS6ZiEQxqoiFyQefZKGeSAweWzlCwsBfvD8ntN2Y:1wDRjO:2A7qqyhYR2_EDMOXxpJrfNWhr9hQBt5iBDy12UbAF10','2026-04-30 18:46:26.825963'),('r0wmddwv25z6hbkfa3598f6qy0nitntp','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1wOaS7:p_uebG1i0b9YWxhMwMIoAaezsN8wEePIGxYuONyrfSA','2026-05-31 12:18:39.441101'),('simb3r12rgyr8lyy6royse3u4c8qr3rq','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vTzdM:9wuzMlBa6bGyMvCvtZigtkHJZ09LVRZAmHkaIaqFOQ8','2025-12-26 09:40:20.342925'),('suy2xw9ouz532todnxfb8qofpqeqrqwe','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1v0xMf:MowAagjOHf8PBQDiMi6LLPerDuS2-njF8CdhH469F4o','2025-10-07 07:23:05.991425'),('tcmelymokqynb3lowdaw13i3ne6mctpd','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1wCMIA:mLwaUoqY2JYb1gzAardObBbry5teYI3TVk_miV9mM3Q','2026-04-27 18:45:50.786893'),('ti6rfi4hixletjps2usk0tmfvt3pd7fb','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1wPPa5:NNXNQ4GGtgmm0LSRsuWLCFysDJ0f3K7SNZbYGwRSHUI','2026-06-02 18:54:17.126720'),('ucqx4witpjorcroa2bfwvxpxfuzs0n92','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vuyqf:eA3zgk3XKkGk2y7DG17-vu0jSJOWWatYhMip9JCoufo','2026-03-10 20:17:37.314261'),('ue5dcwvd8jlw61d29wx8rau1fh466i4x','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vq8E8:ZMzM3EdJlEqFhFZZ93ctMynI7i_0LgAC9cIedD2RmSM','2026-02-25 11:17:48.688260'),('up4qygzkowha3kmjfvsn7fs4ayvg94ej','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1v1lGF:wEqh0uEhgMqw1AG7dE-B9XRCi7QIXbs1Y27cSK4ypZM','2025-10-09 12:39:47.986746'),('us28ktm45qwazizmt1ezgiq5jldg8haf','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vSuYU:viUwCEgQcBfrWlUCEmAyiKRBTtguQMNW8Y5UpMCZd3s','2025-12-23 10:02:50.618457'),('uylsctr6saoziu5o3j9d6z9jc4pggi26','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vqFTL:NupvRcZmiakdDEHMntK_QsgtBe4B0yy0mfaN3WwhsMY','2026-02-25 19:01:59.239593'),('vbfhssrrzxdojbouaupitr4wzgyw5p14','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1uzZWX:Brx_PkMem2FfqyDBvEaUYkLC_aEkvZa0xubReKj-JiQ','2025-10-03 11:43:33.944470'),('vqgiiuo4hmzbafwhy67zhgbi3rgycyyw','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vcgoT:UfcdBegDFUnqzmsrLp0yhP9OJ3VFxJ9IlO1JN5ObWnA','2026-01-19 09:23:45.574943'),('vsmx0mhqy6ug71c20ehsw1rbmwojpv3l','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1wNyWs:dTNka3IMIztHVO8tUCDJZTpFkXS7uaaWU4dzj63VWt4','2026-05-29 19:49:02.784196'),('wdxr07t4ww8lhlxsq3zfrya6h7jhinbo','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vXg1t:AWaS4HbqUu9tceMip3fCjQmPxEx_csDZsmbOUU-ZGro','2026-01-05 13:32:53.341842'),('wncrut47x3bktvlmaq49pzb1mn3z77cb','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1w2bXr:_gbjlm-Pq1faLsynSF9JS-C10jYhOJaxkoOtJJ52G60','2026-03-31 21:01:43.284079'),('xg7j5irb1obqrxnrdfz5q74v61qhvh4m','.eJxVjEEOwiAQRe_C2hAYHKAu3fcMZBhAqoYmpV0Z765NutDtf-_9lwi0rTVsPS9hSuIijDj9bpH4kdsO0p3abZY8t3WZotwVedAuxznl5_Vw_w4q9fqtWfkEqAGMimish8ExaYoaS6ZiEQxqoiFyQefZKGeSAweWzlCwsBfvD8ntN2Y:1w02aI:lPiX9QQ45m6z2IsGmRTzV4qzxDMWqxePT_qE-yewpNA','2026-03-24 19:17:38.608920'),('xr9f4th80uj5lcqhsr4nfo87oilfyidj','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vTdAO:R9TNTirEzApyVlMbaSiTAwk8bWaEJbyEUOL8CvPSq60','2025-12-25 09:40:56.210810'),('xsmr2wvie4xzgnjkdlh84lqmfj4191cf','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vfyUn:ns-sDMhRE7NKaduyFdXvi48zQH8o2eOgPr1AGE97Gb8','2026-01-28 10:53:01.904413'),('yx8jvink9m31cjtwqiu8noar6thiwynb','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vYIiK:g4vz4Ikqkd7oTnKFbelSAfHGQyuPe24Qt8_eeQzssYo','2026-01-07 06:51:16.361451'),('zl55fj2bpxd1xh4cqwvelod9smw8exkd','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vgIlc:OdDi9syjTmYSWvCJTPl0BGQ0yjkiWIqxn05O9IU4K80','2026-01-29 08:31:44.594953'),('zmc6q68j2c8u41mefz02y8ggug3in7ez','.eJxVjDkOwjAUBe_iGln2jxdBSc8ZLP_FOIAcKU6qiLtDpBTQvpl5m0p5XWpau8xpZHVRVp1-N8z0lLYDfuR2nzRNbZlH1LuiD9r1bWJ5XQ_376DmXr-1BzBUhNhlLyXEAcBHK4EceGcNDtk4CcWfgVg8UqSIjqMADsUisnp_AOXPOH0:1vx8DD:aEkDTghqE1AfodO7u1tm8YHUogxnV5IBiKVu5p3OSrY','2026-03-16 18:41:47.270882');
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
  `body` text,
  `attachment` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email_id` (`email_id`),
  KEY `assigned_user_id` (`assigned_user_id`),
  CONSTRAINT `email_delegation_ibfk_1` FOREIGN KEY (`assigned_user_id`) REFERENCES `auth_user` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `email_delegation`
--

LOCK TABLES `email_delegation` WRITE;
/*!40000 ALTER TABLE `email_delegation` DISABLE KEYS */;
INSERT INTO `email_delegation` VALUES (1,'AAMkADg2OGY2NWFlLWRhNjYtNDlhMC1iZTQ2LWRkMGE1N2UzOWNiNQBGAAAAAAC7eQ17N3wvRLFfiCDoqvYFBwAly1laiuoSQJjzgQVvpV6IAAAAAAEMAAAly1laiuoSQJjzgQVvpV6IAAY3SksnAAA=','Withdrawal Vested Claim Documentation: Buyiswa Balakisi (82078510)','SanlamEB@sanlam.co.za',1,'DEL',NULL,1,'Info Only',NULL,'ACVV Aberdeen (PF001)','2026-06-04 15:56:26.000000',NULL,''),(2,'AAMkADg2OGY2NWFlLWRhNjYtNDlhMC1iZTQ2LWRkMGE1N2UzOWNiNQBGAAAAAAC7eQ17N3wvRLFfiCDoqvYFBwAly1laiuoSQJjzgQVvpV6IAAAAAAEMAAAly1laiuoSQJjzgQVvpV6IAAY3SksmAAA=','Withdrawal Vested Claim Documentation: Kerryn-Lee Manuel (82591087)','SanlamEB@sanlam.co.za',NULL,'NEW',NULL,1,NULL,NULL,NULL,'2026-06-04 15:56:25.000000',NULL,''),(3,'AAMkADg2OGY2NWFlLWRhNjYtNDlhMC1iZTQ2LWRkMGE1N2UzOWNiNQBGAAAAAAC7eQ17N3wvRLFfiCDoqvYFBwAly1laiuoSQJjzgQVvpV6IAAAAAAEMAAAly1laiuoSQJjzgQVvpV6IAAY1pPxIAAA=','RE: HUIS AJ LIEBENBERG  LAURENCIA CHRISTIANS','admin@hajl.co.za',NULL,'NEW',NULL,1,NULL,NULL,NULL,'2026-06-04 14:27:34.000000',NULL,''),(4,'AAMkADg2OGY2NWFlLWRhNjYtNDlhMC1iZTQ2LWRkMGE1N2UzOWNiNQBGAAAAAAC7eQ17N3wvRLFfiCDoqvYFBwAly1laiuoSQJjzgQVvpV6IAAAAAAEMAAAly1laiuoSQJjzgQVvpV6IAAY1pPw9AAA=','PF034 : S Francis (Membership Nr : 74345627 ) 30/06/2026 Retirement - Claim Incomplete - Consent Form Outstanding','fin.ejtehuis@acvv.org.za',NULL,'NEW',NULL,1,NULL,NULL,NULL,'2026-06-04 12:30:51.000000',NULL,''),(5,'AAMkADg2OGY2NWFlLWRhNjYtNDlhMC1iZTQ2LWRkMGE1N2UzOWNiNQBGAAAAAAC7eQ17N3wvRLFfiCDoqvYFBwAly1laiuoSQJjzgQVvpV6IAAAAAAEMAAAly1laiuoSQJjzgQVvpV6IAAY1pPw7AAA=','PF034 : G Bonnet ( 72802528 ) 31/05/2026 Retirment','fin.ejtehuis@acvv.org.za',NULL,'NEW',NULL,1,NULL,NULL,NULL,'2026-06-04 12:29:00.000000',NULL,''),(6,'AAMkADg2OGY2NWFlLWRhNjYtNDlhMC1iZTQ2LWRkMGE1N2UzOWNiNQBGAAAAAAC7eQ17N3wvRLFfiCDoqvYFBwAly1laiuoSQJjzgQVvpV6IAAAAAAEMAAAly1laiuoSQJjzgQVvpV6IAAYz7oG3AAA=','Re: [EXTERNAL] RE: PF147 : I Itopo-Bola ( 79716016 ) = Member Emergency Savings Pot Withdrawal  [<AD820527>]','SCDigitalSupport@sanlam.co.za',NULL,'NEW',NULL,1,NULL,NULL,NULL,'2026-06-01 12:26:44.000000',NULL,''),(7,'AAMkADg2OGY2NWFlLWRhNjYtNDlhMC1iZTQ2LWRkMGE1N2UzOWNiNQBGAAAAAAC7eQ17N3wvRLFfiCDoqvYFBwAly1laiuoSQJjzgQVvpV6IAAAAAAEMAAAly1laiuoSQJjzgQVvpV6IAAYyP9X1AAA=','RE: ACVV :  Hompie Kedompie Pension Fund - NEW PAYPOINT','Crystal.Morgan@sanlam.co.za',NULL,'NEW',NULL,1,NULL,NULL,NULL,'2026-05-28 10:31:11.000000',NULL,''),(8,'AAMkADg2OGY2NWFlLWRhNjYtNDlhMC1iZTQ2LWRkMGE1N2UzOWNiNQBGAAAAAAC7eQ17N3wvRLFfiCDoqvYFBwAly1laiuoSQJjzgQVvpV6IAAAAAAEMAAB2K7E2DEtxT54Tmla2xS7uAAYDZkaWAAA=','RE: REINSTATEMENT : ACVV Rusoord Tehuis vir Oues van Dae Paarl ( 1705092.113) PF105 = 85210107','Contributionsupport@sanlam.co.za',NULL,'NEW',NULL,1,NULL,NULL,NULL,'2026-04-24 10:30:54.000000',NULL,'');
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
  `TEL` varchar(50) DEFAULT NULL,
  `TEL 2` varchar(50) DEFAULT NULL,
  `MG ADDRESS` varchar(255) DEFAULT NULL,
  `NPO CODE` varchar(100) DEFAULT NULL,
  `MG BANK INFO` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `global acvv`
--

LOCK TABLES `global acvv` WRITE;
/*!40000 ALTER TABLE `global acvv` DISABLE KEYS */;
INSERT INTO `global acvv` VALUES ('ACVV Aberdeen (PF001)','PF001','15','Active','12,660.50','','','','','aalwynhofacvv@gmail.com,Luano@gmail.com','','','','',''),('ACVV Uitenhage ACVV Dienstak (PF002)','PF002','76','Active','68,404.27','','','','','acvvaandmymering@acvv.org.za','0419921510','456456','456456','456456','456456'),('ACVV Malmesbury Aandskemering (PF003)','PF003','51','Active','56,491.76','','','','','personeel@cornergate.com','0224821466','',NULL,NULL,NULL),('ACVV Piketberg Huis AJ Liebenberg (PF004)','PF004','24','Active','28,268.04','01.05.2026','','','','marelisevercuiel@gmail.com','','','','',''),('ACVV Algoapark (PF005)','PF005','6','Active','12,467.25','','','','','acvvcwoods@gmail.com','','',NULL,NULL,NULL),('ACVV Williston (PF006)','PF006','11','Active','9,699.00','01.05.2026','','','','finans.amandel@hantam.co.za','0533913185','',NULL,NULL,NULL),('ACVV Azaleahof ACVV Dienssentrum Dienstak (PF007)','PF007','34','Active','61,846.20','','','','','azaleahofacc@adept.co.za','','',NULL,NULL,NULL),('ACVV Olifantshoek Bergen Rus (PF008)','PF008','28','Active','27,669.15','','','','','ajroelofse2@gmail.com','','',NULL,NULL,NULL),('ACVV Riebeek Wes Huis Bergsig (PF009)','PF009','33','Active','39,244.57','','','','','fin.huisbergsig@acvv.org.za;ontvangs@huisbergsig.co.za','0224612721','',NULL,NULL,NULL),('ACVV Bothasig Creche Dienstak (PF010)','PF010','21','Active','21,971.25','','','','','antoinettebrand775@gmail.com','0215584314','',NULL,NULL,NULL),('ACVV Bredasdorp (PF011)','PF011','3','Active','6,594.86','','','','','rekeninge1@suideroord.co.za','0284241080','',NULL,NULL,NULL),('ACVV Bredasdorp Suidpunt Diens (PF012)','PF012','2','Active','3,196.20','','','','','rekeninge1@suideroord.co.za','0284241080','',NULL,NULL,NULL),('ACVV Bright Lights (PF013)1705092.014','PF013','0','NO MEMBERS','-','','','','','','','',NULL,NULL,NULL),('ACVV Caledon (PF014)','PF014','11','Active','12,709.97','','','','','fin.acvvdagsorg@gmail.com;finans.heidehof@twk.co.za','0233161505','',NULL,NULL,NULL),('ACVV','PF015','0','NO MEMBERS','-','','','','','','','',NULL,NULL,NULL),('ACVV Carnarvon (PF017)','PF017','0','NO MEMBERS','-','','','','','','','',NULL,NULL,NULL),('ACVV Ceres (PF018)','PF018','5','Active','8,747.95','','','','','fin.ceres@acvv.org.za;acvv.ceres@outlook.com','','',NULL,NULL,NULL),('ACVV Adelaide (PF019)','PF019','35','Active','24,908.05','','','','','aurelialoots@yahoo.com','','',NULL,NULL,NULL),('ACVV Cradock (PF020)','PF020','10','Active','11,894.70','','','','','cradock@acvv.org.za','','',NULL,NULL,NULL),('ACVV Britstown (PF021)','PF021','16','Active','13,120.81','','','','','acvvhuisdaneel@gmail.com','','',NULL,NULL,NULL),('ACVV Carnarvon Huis Danie van Huyssteen (PF022)','PF022','16','Active','11,138.54','','','','','huisdanie003805@gmail.com','','',NULL,NULL,NULL),('ACVV De Aar (PF023)','PF023','4','Active','7,634.06','','','','','fin.acvvdeaar@acvv.org.za','0649828803','',NULL,NULL,NULL),('ACVV De Aar Lollapot (PF023B)','PF023B','8','Active','18,118.38','','','','','elzaan@deaarsa.co.za','','',NULL,NULL,NULL),('ACVV De Grendel ACVV Dienstak (PF024)','PF024','16','Active','13,455.81','','','','','acvvdegrendel@acvv.org.za','','',NULL,NULL,NULL),('ACVV Delft Dienstak (PF025)','PF025','8','Active','7,351.95','','','','','acvvlabelle-fin@acvv.org.za','0219482019','',NULL,NULL,NULL),('ACVV Despatch Dienssentrum (PF026)','PF026','1','Active','851.49','','','','','dienssentrum2@telkomsa.net','','',NULL,NULL,NULL),('ACVV Alexandria (PF027)','PF027','35','Active','33,522.75','','','','','fin.huisdiaz@acvv.org.za;Acvvhuisdiaz@outlook.com','','',NULL,NULL,NULL),('ACVV Tulbagh (PF028)','PF028','23','Active','22,577.40','','','','','bestuurder.huisdisa@acvv.org.za;fin.huisdisa@acvv.org.za','','',NULL,NULL,NULL),('ACVV Richmond Driefontein Dienssentrum (PF030)','PF030','0','NO MEMBERS','-','','','','','','','',NULL,NULL,NULL),('ACVV Dysselsdorp (PF031)','PF031','6','Active','10,107.72','','','','','acvvfinansies@scwireless.co.za','0442516721','0624054918',NULL,NULL,NULL),('ACVV Edelweiss ACVV Dienssentrum en Wooneenhede Dienstak (PF032)','PF032','21','Active','33,451.50','','','','','acvvedelweiss@acvv.org.za','0219761150','',NULL,NULL,NULL),('ACVV Eldorado Dienstak (PF033)','PF033','0','NO MEMBERS','-','','','','','','','',NULL,NULL,NULL),('ACVV Cradock Elizabeth Jordaan (PF034)','PF034','37','Active','37,872.39','','','','','fin.ejtehuis@acvv.org.za;finans.heidehof@twk.co.za','0488811857','',NULL,NULL,NULL),('ACVV Franschhoek Fleur de Lis (PF035)','PF035','17','Active','18,658.05','','','','','fin.acvvfleur@acvv.org.za;admin@acvvfleur.co.za','0218762411','',NULL,NULL,NULL),('ACVV Franschhoek (PF036)','PF036','3','Active','7,205.10','','','','','sandra@wemz.co.za;admin@acvvfrans.org.za;fin@acvvfrans.org.za','0210231298','',NULL,NULL,NULL),('ACVV Victoria Wes (PF037)','PF037','17','Active','11,126.00','','','','','vicwesacvv2@gmail.com;elsdenise3@gmail.com;ngkerkvicwes@gmail.com','','',NULL,NULL,NULL),('ACVV Port Elizabeth Wes Huis Genot (PF038)','PF038','51','Active','45,337.90','','','','','fin.huisgenot@acvv.org.za','','',NULL,NULL,NULL),('ACVV George (PF039)','PF039','49','Active','75,233.93','','','','','accountsgrg@acvv.org.za','','',NULL,NULL,NULL),('ACVV Grabouw (PF040)','PF040','6','Active','16,364.47','','','','','fin.huisgroenland@acvv.org.za;manager@huisgroenland.co.za','0218594209','',NULL,NULL,NULL),('ACVV Grabouw Huis Groenland (PF041)','PF041','16','Active','24,007.50','','','','','fin.huisgroenland@acvv.org.za;manager@huisgroenland.co.za','0218594209','',NULL,NULL,NULL),('ACVV Grahamstad (PF042)','PF042','0','NO MEMBERS','-','','','','','fin.grahamstad@acvv.org.za','','',NULL,NULL,NULL),('ACVV Newton Park PE Haas Das Creche (PF043)','PF043','14','Active','11,651.97','','','','','johanbeukman.irispark@gmail.com','','',NULL,NULL,NULL),('ACVV Caledon Heidehof (PF044)','PF044','33','Active','44,029.65','','','','','finans.heidehof@twk.co.za;admin.heidehof@twk.co.za;bestuurder.heidehof@twk.co.za','0282141755','',NULL,NULL,NULL),('ACVV Heidelberg (PF045)','PF045','3','Active','2,807.31','','','','','hshfinansies@gmail.com','0287221384','',NULL,NULL,NULL),('ACVV Griekwastad (PF046)','PF046','15','Active','11,788.50','','','','','huisheldersig@yahoo.co.za','0533430228','',NULL,NULL,NULL),('ACVV Beaufort-Wes (PF047)','PF047','51','Active','50,026.50','','','','','acvvhesperos@beaufortwest.net','0234143465','',NULL,NULL,NULL),('ACVV Hoofbestuur (PF048)','PF048','24','Active','154,813.46','','','','','andre@acvv.org.za','0214617437','',NULL,NULL,NULL),('ACVV Pofadder Huis Sophia (PF049)','PF049','13','Active','11,110.18','','','','','acvvsophiatehuis@acvv.org.za','0549330297','',NULL,NULL,NULL),('ACVV Strand Huis Jan Swart (PF051)','PF051','22','Active','29,134.80','','','','','accounts@huisjs.co.za','021 8543763','',NULL,NULL,NULL),('ACVV Postmasburg Huis Jan Vorster (PF052)','PF052','17','Active','17,226.02','','','','','roneldip@gmail.com;huisjanvorster@outlook.com','','',NULL,NULL,NULL),('ACVV Tak Kaapstad (PF053)','PF053','29','Active','47,123.72','','','','','admin@acvvct.org.za;Aaccounts@acvvpen.co.za','','',NULL,NULL,NULL),('ACVV Kimberley (PF054)','PF054','4','Active','6,683.40','','','','','frans@acvv-kimberley.co.za','0538421141','',NULL,NULL,NULL),('ACVV Kimberley Speelgoedland (PF055)','PF055','0','NO MEMBERS','-','','','','','','','',NULL,NULL,NULL),('ACVV Koeberg (PF056)','PF056','5','Active','12,018.90','','','','','dawnsutton397@gmail.com;acvvkoeberg@acvv.org.za','0215532745','',NULL,NULL,NULL),('ACVV Prins Albert Huis Kweekvallei (PF057)','PF057','23','Active','25,835.07','','','','','koenelsabe@gmail.com;huiskweekvallei@acvv.org.za;accounts_hkv@acvv.org.za','0514104200','',NULL,NULL,NULL),('ACVV Kuruman (PF058)','PF058','0','NO MEMBERS','-','','','','','kuruman@acvv.org.za','0537121862','0537121341',NULL,NULL,NULL),('ACVV La Belle ACVV Dienstak (PF059)','PF059','17','Active','26,086.35','','','','','acvvlabelle-fin@acvv.org.za','0219482019','',NULL,NULL,NULL),('ACVV L\'Amour Martinelle Creche (PF060)','PF060','1','Active','1,155.00','','','','','lamourm@wo.co.za','','',NULL,NULL,NULL),('ACVV Magnolia ACVV Dienstak (PF062)','PF062','30','Active','43,903.80','','','','','money@magnoliaacvv.co.za','0219486085','',NULL,NULL,NULL),('ACVV Huis Malan Jacobs ACVV Tehuis vir Bejaardes (PF063)','PF063','20','Active','18,981.30','','','','','hmjlaingsburg@gmail.com','','',NULL,NULL,NULL),('ACVV Malmesbury (PF064)','PF064','12','Active','21,285.68','','','','','mbury.dienssentrum@acvv.org.za','','',NULL,NULL,NULL),('ACVV Somerset Wes Huis Marie Louw (PF065)','PF065','37','Active','47,616.75','','','','','finance@acvvhml.co.za','','',NULL,NULL,NULL),('ACVV Ceres Huis Maudie Kriel (PF066)','PF066','53','Active','60,897.00','','','','','maudie@lando.co.za','','',NULL,NULL,NULL),('ACVV Middelburg Oos-Kaap (PF067)','PF067','7','Active','7,071.30','','','','','yvonne@adsactive.com','','',NULL,NULL,NULL),('ACVV Kuruman Mimosahof (PF068)','PF068','20','Active','18,143.55','','','','','mimosahof1@gmail.com','0824955862','',NULL,NULL,NULL),('ACVV Mitchells Plain (PF069)','PF069','7','Active','14,689.80','','','','','accounts@acvvct.org.za;admin@acvvct.org.za','','',NULL,NULL,NULL),('ACVV Montagu (PF070)','PF070','5','Active','8,874.49','','','','','admin@acvvmontagu.co.za','0236141490','',NULL,NULL,NULL),('ACVV Moorreesburg (PF071)','PF071','37','Active','39,218.83','','','','','huismoorreesfin@pcnetmail.co.za','0224331477','',NULL,NULL,NULL),('ACVV Moreson ACVV Kinder- en Jeugsorgsentrum (PF072)','PF072','27','Active','50,369.10','','','','','moreson.admin@acvv.org.za','0448744798','',NULL,NULL,NULL),('ACVV Mosselbaai (PF073)','PF073','125','Active','138,254.27','','','','','mosselbaaitesourier@acvv.org.za;info@acvv.org.za','','',NULL,NULL,NULL),('ACVV Springbok Huis Namakwaland (PF074)','PF074','40','Active','34,316.62','','','','','finance@huisnamakwaland.co.za','','',NULL,NULL,NULL),('ACVV Despatch Huis Najaar (PF075)','PF075','60','Active','54,100.22','','','','','accounts@huisnajaar.co.za','','',NULL,NULL,NULL),('ACVV Porterville Tak Huis Nerina (PF076)','PF076','32','Active','37,410.45','','','','','fin.huisnerina@acvv.org.za','0229312720','',NULL,NULL,NULL),('ACVV Dordrecht (PF077)','PF077','19','Active','13,945.53','','','','','nerinahof@gmail.com','','',NULL,NULL,NULL),('ACVV Worcester (PF078)','PF078','52','Active','64,251.44','','','','','finansies@nuwerus.co.za','','',NULL,NULL,NULL),('ACVV Paarl Vallei Oase Dienssentrum (PF079)','PF079','3','Active','3,189.75','','','','','info@acvv-pvallei.org.za','0218711515','',NULL,NULL,NULL),('ACVV Kimberley Ons Huis (PF080)','PF080','24','Active','22,097.69','','','','','frans@acvv-kimberley.co.za','0538421141','',NULL,NULL,NULL),('ACVV Ons Tuiste ACVV Dienstak (PF081)','PF081','49','Active','64,510.54','','','','','fin.ons-tuiste@acvv.org.za','','',NULL,NULL,NULL),('ACVV Op die Kruin ACVV Dienstak (PF082)','PF082','10','Active','7,315.80','','','','','acvvopdiekruin@gmail.com','0536313130','4523486',NULL,NULL,NULL),('ACVV Upington Oranjehof Tehuis (PF083)','PF083','30','Active','48,825.60','','','','','admin@acvvoranjehof.co.za','0543312044','0543321986',NULL,NULL,NULL),('ACVV Upington Oranjehof Dienssentrum (PF084)','PF084','0','NO MEMBERS','-','','','','','','','',NULL,NULL,NULL),('ACVV Oudtshoorn (PF085)','PF085','163','Active','153,550.20','','','','','fin.oudtshoorn@acvv.org.za;admin.oudtshoorn@acvv.org.za','0442722211','',NULL,NULL,NULL),('ACVV Paarl (PF086)','PF086','2','Active','5,424.00','','','','','acvvpaarl@gmail.com','0218722738','',NULL,NULL,NULL),('ACVV Noorder-Paal (PF087)','PF087','3','Active','8,767.18','','','','','admin@acvvnp.org.za','','',NULL,NULL,NULL),('ACVV Paarl Vallei (PF088)','PF088','5','Active','13,118.70','','','','','info@acvv-pvallei.org.za','0218711515','',NULL,NULL,NULL),('ACVV Newton Park PE (PF089)','PF089','0','NO MEMBERS','-','','','','','','','',NULL,NULL,NULL),('ACVV PE Noord (PF090)','PF090','0','NO MEMBERS','-','','','','','','','',NULL,NULL,NULL),('ACVV Port Elizabeth Suid (PF092)','PF092','24','Active','40,939.15','','','','','admin@poplarlaan.acvv.co.za;book@pesuid.acvv.co.za','','',NULL,NULL,NULL),('ACVV Port Elizabeth Wes (PF093)','PF093','9','Active','19,032.23','','','','','accounts.pewes@lantic.net','0413602106','',NULL,NULL,NULL),('ACVV Piketberg (PF094)','PF094','3','Active','6,242.17','','','','','fin.piketberg@acvv.org.za','','',NULL,NULL,NULL),('ACVV St Helenabaai (PF095)','PF095','15','Active','14,810.99','','','','','aletta@visagieboerdery.com','','',NULL,NULL,NULL),('ACVV Poplarlaan PE (PF096)','PF096','1','Active','583.07','','','','','admin@poplarlaan.acvv.co.za;book@pesuid.acvv.co.za','0608106260','',NULL,NULL,NULL),('ACVV Porterville Tak (PF097)','PF097','2','Active','1,845.81','','','','','fin.huisnerina@acvv.org.za','0229312720','',NULL,NULL,NULL),('ACVV Postmasburg (PF098)','PF098','4','Active','7,497.73','','','','','pmgacvv@gmail.com','0533132164','',NULL,NULL,NULL),('ACVV Prieska (PF099)','PF099','4','Active','5,808.47','','','','','fin.prieska@acvv.org.za','','',NULL,NULL,NULL),('ACVV Caledon Protea Dienssentrum (PF100)','PF100','1','Active','712.95','','','','','finans.heidehof@twk.co.za','0282141755','',NULL,NULL,NULL),('ACVV Riebeek Kasteel (PF101)','PF101','11','Active','20,102.35','','','','','manager@acvvrk.org','0224481715','',NULL,NULL,NULL),('ACVV Riversdal (PF102)','PF102','14','Active','23,778.62','','','','','info@shovelprojects.co.za','0287131378','',NULL,NULL,NULL),('ACVV Robertson Huis Le Roux (PF103)','PF103','25','Active','25,125.84','','','','','fin.huisleroux@acvv.org.za;fin@acvvrobertson.org.za;','0236263163','',NULL,NULL,NULL),('ACVV Robertson (PF104)','PF104','11','Active','16,340.40','','','','','fin2@acvvrobertson.org.za','0236263097','',NULL,NULL,NULL),('ACVV Rusoord Tehuis vir Oues van Dae Paarl (PF105)','PF105','35','Active','40,184.75','','','','','finansies@rusoordtehuis.co.za;bestuurder@rusoordtehuis.co.za','','',NULL,NULL,NULL),('ACVV Clanwilliam (PF106)','PF106','25','Active','30,845.28','','','','','admin@acvvsederhof.org.za','','',NULL,NULL,NULL),('ACVV Somerset Oos Huis Silwerjare (PF107)','PF107','13','Active','10,690.56','','','','','fin.silwerjare@acvv.org.za','0422432107','',NULL,NULL,NULL),('ACVV Wellington Tak Silwerkruin (PF108)','PF108','67','Active','78,653.35','','','','','finans1@silwerkruin.com','0218731040','',NULL,NULL,NULL),('ACVV Wellington Tak Silwerkruin (PF109)','PF109','0','NO MEMBERS','-','','','','','','','',NULL,NULL,NULL),('ACVV Elizabeth Roos Tehuis Dienstak (PF110)','PF110','16','Active','17,247.30','','','','','bookkeeper.elizabethroos@gmail.com;admin@acvvct.org.za;accounts@acvvct.org.za','0214621638','',NULL,NULL,NULL),('ACVV Skiereiland Beheerkomitee van die ACVV Dienstak (PF111)','PF111','14','Active','27,888.91','','','','','accounts@acvvpen.co.za','','',NULL,NULL,NULL),('ACVV Strand Soeterus Tehuis (PF112)','PF112','13','Active','16,355.10','','','','','finansies@soeterus.com','0218537423','',NULL,NULL,NULL),('ACVV Lambersbaai Somerkoelte Tehuis (PF113)','PF113','36','Active','32,347.50','','','','','somerkoelte.finansies@gmail.com','','',NULL,NULL,NULL),('ACVV Somerset Oos','PF114','0','NO MEMBERS','-','','','','','','','',NULL,NULL,NULL),('ACVV Somerset Wes (PF115)','PF115','4','Active','8,094.90','','','','','acvvswes@telkomsa.net','0218522103','',NULL,NULL,NULL),('ACVV Somerset Oos Dienssentrum (PF116)','PF116','0','NO MEMBERS','-','','','','','','','',NULL,NULL,NULL),('ACVV De Aar Sonder Sorge Tehuis (PF117)','PF117','24','Active','21,384.15','','','','','truteriana@gmail.com;sondersorge.acvv@gmail.com','','',NULL,NULL,NULL),('ACVV Calvinia (PF118)','PF118','33','Active','30,436.33','','','','','sorgvliet@hantam.co.za','0273411223','',NULL,NULL,NULL),('ACVV Malmesbury Speelkasteel Creche (PF119)','PF119','0','NO MEMBERS','-','','','','','','','',NULL,NULL,NULL),('ACVV Strand Speelkasteel (PF120)','PF120','17','Active','19,272.00','','','','','speelkasteelstrandboekhouer@acvv.org.za;speelkasteelstrand@acvv.org.za;speelkasteelprincipal@acvv.org.za','','',NULL,NULL,NULL),('ACVV Douglas (PF121)','PF121','34','Active','41,566.55','','','','','fin.spesbona@acvv.org.za','0532981035','',NULL,NULL,NULL),('ACVV Springbok (PF122)','PF122','0','NO MEMBERS','-','','','','','','','',NULL,NULL,NULL),('ACVV Stellenbosch (PF123)','PF123','20','Active','35,187.50','','','','','fin.stellenbosch@acvv.org.za','0218876959','',NULL,NULL,NULL),('ACVV Worcester Stilwaters Dienssentrum (PF124)','PF124','5','Active','6,818.10','','','','','stilwatersfin@acvvcw.co.za','0233420634','',NULL,NULL,NULL),('ACVV Die Afrikaanse Christelike Vrouevereniging Strand (PF125)','PF125','12','Active','27,332.10','','','','','strandadmin@acvv.org.za','0218547215','',NULL,NULL,NULL),('ACVV Bredasdorp Suideroord Tehuis (PF126)','PF126','98','Active','134,729.40','','','','','rekeninge1@suideroord.co.za','0284241080','',NULL,NULL,NULL),('ACVV Swellendam (PF127)','PF127','4','Active','8,341.95','','','','','fin.swellendam@acvv.org.za','','',NULL,NULL,NULL),('ACVV Kom Nader Dienssentrum Swellendam (PF128)','PF128','0','NO MEMBERS','-','','','','','','','',NULL,NULL,NULL),('ACVV Touwsrivier (PF129)','PF129','0','NO MEMBERS','-','','','','','','','',NULL,NULL,NULL),('ACVV Middelburg Oos Kaap Huis Karee (PF130)','PF130','9','Active','11,417.70','','','','','huiskaree@gmail.com','0498422151','',NULL,NULL,NULL),('ACVV Upington (PF131)','PF131','6','Active','8,785.85','','','','','adminupt@wjatrust.co.za','','',NULL,NULL,NULL),('ACVV Utopia ACVV Tehuis vir Bejaardes Dienstak (PF132)','PF132','13','Active','28,343.24','','','','','anneen@utopiastb.co.za;annelie@ffas.co.za;admin@utopiastb.co.za;lilabotha1602@gmail.com','','',NULL,NULL,NULL),('ACVV Kirkwood Valleihof Tehuis (PF133)','PF133','32','Active','34,685.07','','','','','fin.valleihof@acvv.org.za','0422300393','',NULL,NULL,NULL),('ACVV Graaff-Reinet Huis van de Graaff Tehuis (PF134)','PF134','21','Active','21,928.93','','','','','acvvgraaffreinet@telkomsa.net','0498923229','',NULL,NULL,NULL),('ACVV Huis Van Niekerk Benadehof ACVV Dienssentrum Dienstak (PF135)','PF135','46','Active','83,154.65','','','','','finansies@vnbh.org.za','0218531040','0218531041',NULL,NULL,NULL),('ACVV Huis Vergenoegd Dienstak Diens en Dag (Paarl) (PF136)','PF136','3','Active','14,454.68','','','','','hvg1@lando.co.za','','',NULL,NULL,NULL),('ACVV Huis Vergenoegd Dienstak Siekeboeg (Paarl) (PF137)','PF137','75','Active','113,465.46','','','','','hvg1@lando.co.za','','',NULL,NULL,NULL),('ACVV Huis Vergenoegd Dienstak Woonstelle (Paarl) (PF138)','PF138','28','Active','41,624.86','','','','','hvg1@lando.co.za','','',NULL,NULL,NULL),('ACVV Wellington Tak (PF139)','PF139','3','Active','6,594.90','','','','','well.admin@acvv.org.za','0218732204','',NULL,NULL,NULL),('ACVV Wellington Tak Fyngoud Dienssentrum (PF140)','PF140','2','Active','3,532.50','','','','','acvvfyngoud@acvv.org.za','','',NULL,NULL,NULL),('ACVV Paarl Vallei Wielie Walie Creche (PF141)','PF141','5','Active','5,031.00','','','','','info@acvv-pvallei.org.za','0218711515','',NULL,NULL,NULL),('ACVV Weskusnessie Dienstak (PF142)','PF142','23','Active','24,938.50','','','','','lizlryan@gmail.com','','',NULL,NULL,NULL),('ACVV Danielskuil (PF143)','PF143','7','Active','6,226.22','','','','','acvvdanielskuil@gmail.com','','',NULL,NULL,NULL),('ACVV Victoria Wes Wiekie Wessie Creche (PF144)','PF144','1','Active','748.50','','','','','vicwesacvv2@gmail.com;elsdenise3@gmail.com;ngkerkvicwes@gmail.com','','',NULL,NULL,NULL),('ACVV Worcester (PF145)','PF145','5','Active','15,141.30','','','','','stilwatersfin@acvvcw.co.za','0233420634','',NULL,NULL,NULL),('ACVV Ysterplaat Dienstak van die ACVV (PF146)','PF146','29','Active','33,194.75','','','','','finances@homeriaabel.co.za','0215118119','',NULL,NULL,NULL),('ACVV Zonnebloem ACVV Dienstak (PF147)','PF147','49','Active','45,585.90','','','','','zonnebloemfinansies@acvv.org.za','','',NULL,NULL,NULL),('ACVV Strand Dienssentrum vir Seniors (PF148)','PF148','3','Active','6,834.60','','','','','admin@strandsds.co.za;info@strandsds.co.za','','',NULL,NULL,NULL),('ACVV Grabouw Appelkontrei Dienssentrum (PF149)','PF149','1','Active','1,609.20','','','','','fin.huisgroenland@acvv.org.za;manager@huisgroenland.co.za','0218594209','',NULL,NULL,NULL),('ACVV Reivilo Dienssentrum (PF150)','PF150','7','Active','3,045.00','','','','','leone.jansenvanvuuren@gmail.com;doretteweideman@gmail.com','','',NULL,NULL,NULL),('ACVV Elandsbaai (PF151)','PF151','3','Active','3,183.93','','','','','marlise@smitrek.co.za','0609957365','',NULL,NULL,NULL),('ACVV Colesberg Old Age Home (PF155)','PF155','7','Active','8,029.04','','','','','huiskiepersol1@gmail.com','','',NULL,NULL,NULL),('ACVV Triomf Child Care Centre (PF156)','PF156','7','Active','5,961.38','','','','','sharon@thebarn.co.za','','',NULL,NULL,NULL),('ACVV Barrydale (PF157)','PF157','1','Active','1,170.90','','','','','fin.barrydale@acvv.org.za','0285721995','0711279004',NULL,NULL,NULL),('ACVV Carnarvon Karavaantjie Kleuterskool (PF159)','PF159','0','NO MEMBERS','-','','','','','','','',NULL,NULL,NULL),('ACVV Carnarvon Marcia Louw Kleuterskool (PF160)','PF160','0','NO MEMBERS','-','','','','','','','',NULL,NULL,NULL),('ACVV Malmesbury Dienssentrum (PF161)','PF161','0','NO MEMBERS','-','','','','','mbury.dienssentrum@acvv.org.za','','',NULL,NULL,NULL),('ACVV Malmesbury Naskool (PF162)','PF162','0','NO MEMBERS','-','','','','','','','',NULL,NULL,NULL),('ACVV Somerset Wes Tinktinkie (PF163)','PF163','5','Active','5,314.95','','','','','acvvswes@telkomsa.net','0218522103','',NULL,NULL,NULL),('ACVV Somerset Wes Versorgingsoord Heidi (PF164)','PF164','0','NO MEMBERS','-','','','','','','','',NULL,NULL,NULL),('ACVV Despatch (PF165)','PF165','0','NO MEMBERS','-','','','','','','','',NULL,NULL,NULL),('ACVV Kuruman Heuwelsig (PF166)','PF166','3','Active','4,601.14','','','','','fin.heuwelsig@acvv.org.za','0537120447','',NULL,NULL,NULL),('ACVV Oudtshoorn Emmanuel Verpleegskool (PF167)','PF167','0','NO MEMBERS','-','','','','','','','',NULL,NULL,NULL),('ACVV Port Elizabeth Sentraal Khayalethu Jeugsentrum (PF168)','PF168','9','Active','21,783.75','','','','','bookkeeper@khayalethu.org.za','0414845667','',NULL,NULL,NULL),('ACVV Piketberg Trippe Trappe (PF169)','PF169','5','Active','4,281.75','','','','','fin.piketberg@acvv.org.za','','',NULL,NULL,NULL),('ACVV Poplarlaan PE Pikkewyntjie (PF170)','PF170','0','NO MEMBERS','-','','','','','','','',NULL,NULL,NULL),('ACVV Robertson Jakaranda Dienssentrum (PF171)','PF171','3','Active','4,413.00','','','','','fin2@acvvrobertson.org.za','0236263097','',NULL,NULL,NULL),('ACVV Worcester Bollieland Creche (PF172)','PF172','9','Active','8,378.55','','','','','fin.bollieland@acvv.org.za','0233420760','',NULL,NULL,NULL),('ACVV Moorreesburg Kleuterland (PF173)','PF173','10','Active','10,711.80','','','','','huismoorreesfin@pcnetmail.co.za','0224331477','',NULL,NULL,NULL),('ACVV Moorreesburg (PF174)','PF174','4','Active','7,765.80','','','','','huismoorreesfin@pcnetmail.co.za','0224331477','',NULL,NULL,NULL),('ACVV Dienssentrum Moorreesburg (PF175)','PF175','2','Active','2,168.64','','','','','huismoorreesfin@pcnetmail.co.za','0224331477','',NULL,NULL,NULL),('ACVV Moorreesburg Heuwelsig (PF176)','PF176','0','NO MEMBERS','-','','','','','','0224331477','',NULL,NULL,NULL),('ACVV Klein Moorrees Moorreesburg (PF177)','PF177','0','NO MEMBERS','-','','','','','','','',NULL,NULL,NULL),('ACVV Chrisbahof Moorreesburg (PF178)','PF178','0','NO MEMBERS','-','','','','','','','',NULL,NULL,NULL),('ACVV Irispark (PF179)','PF179','1','Active','771.11','','','','','johanbeukman.irispark@gmail.com','','',NULL,NULL,NULL),('ACVV Marinerylaan (PF180)','PF180','1','Active','1,236.00','','','','','johanbeukman.irispark@gmail.com','','',NULL,NULL,NULL),('ACVV Dysselsdorp Swartberg Dienssentrum (PF181)','PF181','2','Active','1,596.08','','','','','acvvfinansies@scwireless.co.za','0442516721','0624054918',NULL,NULL,NULL),('ACVV Dysselsdorp Siembamba Creche (PF182)','PF182','5','Active','4,174.50','','','','','acvvfinansies@scwireless.co.za','0442516721','0624054918',NULL,NULL,NULL),('ACVV Yzerfontein','PF183','1','Active','1,635.00','','','','','acvvyzerfontein@gmail.com','0224512494','',NULL,NULL,NULL),('ACVV Dysselsdorp Shelter (PF184)','PF184','4','Active','4,948.26','','','','','acvvfinansies@scwireless.co.za','0442516721','0624054918',NULL,NULL,NULL),('ACVV Riebeek Wes Humanitas (PF185)','PF185','2','Active','1,497.96','','','','','fin.riebeekwes@acvv.org.za','0224612721','',NULL,NULL,NULL),('ACVV Port Elizabeth Sentraal (PF186)','PF186','0','NO MEMBERS','-','','','','','','','',NULL,NULL,NULL),('ACVV New Branch Placeholder','PFXXX','0','Active','0.00',NULL,NULL,NULL,'No info','placeholder@mail.com','-','-',NULL,NULL,NULL);
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `reconciliation_record`
--

LOCK TABLES `reconciliation_record` WRITE;
/*!40000 ALTER TABLE `reconciliation_record` DISABLE KEYS */;
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
  `lpi_amount` decimal(15,2) DEFAULT '0.00',
  `reconciled_status` varchar(50) DEFAULT 'Unreconciled',
  `date_schedule_received` date DEFAULT NULL,
  `date_confirmed_on_step` date DEFAULT NULL,
  `debit_order_date` date DEFAULT NULL,
  `lpi_reason` varchar(100) DEFAULT NULL,
  `debit_order_success` varchar(10) DEFAULT NULL,
  `is_closed` tinyint(1) DEFAULT '0',
  `closed_at` datetime(6) DEFAULT NULL,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `updated_by_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_fiscal_mg` (`fiscal_month`,`mg_code`)
) ENGINE=InnoDB AUTO_INCREMENT=359 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `reconciliation_worksheet`
--

LOCK TABLES `reconciliation_worksheet` WRITE;
/*!40000 ALTER TABLE `reconciliation_worksheet` DISABLE KEYS */;
INSERT INTO `reconciliation_worksheet` VALUES (1,'2026-05-01','ACVV Aberdeen (PF001)','PF001','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:38',NULL),(2,'2026-05-01','ACVV Uitenhage ACVV Dienstak (PF002)','PF002','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:38',NULL),(3,'2026-05-01','ACVV Malmesbury Aandskemering (PF003)','PF003','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:38',NULL),(4,'2026-05-01','ACVV Piketberg Huis AJ Liebenberg (PF004)','PF004','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:38',NULL),(5,'2026-05-01','ACVV Algoapark (PF005)','PF005','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:38',NULL),(6,'2026-05-01','ACVV Williston (PF006)','PF006','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:38',NULL),(7,'2026-05-01','ACVV Azaleahof ACVV Dienssentrum Dienstak (PF007)','PF007','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:38',NULL),(8,'2026-05-01','ACVV Olifantshoek Bergen Rus (PF008)','PF008','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:38',NULL),(9,'2026-05-01','ACVV Riebeek Wes Huis Bergsig (PF009)','PF009','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:38',NULL),(10,'2026-05-01','ACVV Bothasig Creche Dienstak (PF010)','PF010','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(11,'2026-05-01','ACVV Bredasdorp (PF011)','PF011','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(12,'2026-05-01','ACVV Bredasdorp Suidpunt Diens (PF012)','PF012','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(13,'2026-05-01','ACVV Bright Lights (PF013)1705092.014','PF013','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(14,'2026-05-01','ACVV Caledon (PF014)','PF014','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(15,'2026-05-01','ACVV','PF015','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(16,'2026-05-01','ACVV Carnarvon (PF017)','PF017','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(17,'2026-05-01','ACVV Ceres (PF018)','PF018','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(18,'2026-05-01','ACVV Adelaide (PF019)','PF019','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(19,'2026-05-01','ACVV Cradock (PF020)','PF020','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(20,'2026-05-01','ACVV Britstown (PF021)','PF021','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(21,'2026-05-01','ACVV Carnarvon Huis Danie van Huyssteen (PF022)','PF022','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(22,'2026-05-01','ACVV De Aar (PF023)','PF023','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(23,'2026-05-01','ACVV De Aar Lollapot (PF023B)','PF023B','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(24,'2026-05-01','ACVV De Grendel ACVV Dienstak (PF024)','PF024','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(25,'2026-05-01','ACVV Delft Dienstak (PF025)','PF025','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(26,'2026-05-01','ACVV Despatch Dienssentrum (PF026)','PF026','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(27,'2026-05-01','ACVV Alexandria (PF027)','PF027','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(28,'2026-05-01','ACVV Tulbagh (PF028)','PF028','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(29,'2026-05-01','ACVV Richmond Driefontein Dienssentrum (PF030)','PF030','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(30,'2026-05-01','ACVV Dysselsdorp (PF031)','PF031','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(31,'2026-05-01','ACVV Edelweiss ACVV Dienssentrum en Wooneenhede Dienstak (PF032)','PF032','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(32,'2026-05-01','ACVV Eldorado Dienstak (PF033)','PF033','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(33,'2026-05-01','ACVV Cradock Elizabeth Jordaan (PF034)','PF034','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(34,'2026-05-01','ACVV Franschhoek Fleur de Lis (PF035)','PF035','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(35,'2026-05-01','ACVV Franschhoek (PF036)','PF036','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(36,'2026-05-01','ACVV Victoria Wes (PF037)','PF037','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(37,'2026-05-01','ACVV Port Elizabeth Wes Huis Genot (PF038)','PF038','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(38,'2026-05-01','ACVV George (PF039)','PF039','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(39,'2026-05-01','ACVV Grabouw (PF040)','PF040','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(40,'2026-05-01','ACVV Grabouw Huis Groenland (PF041)','PF041','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(41,'2026-05-01','ACVV Grahamstad (PF042)','PF042','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(42,'2026-05-01','ACVV Newton Park PE Haas Das Creche (PF043)','PF043','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(43,'2026-05-01','ACVV Caledon Heidehof (PF044)','PF044','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(44,'2026-05-01','ACVV Heidelberg (PF045)','PF045','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(45,'2026-05-01','ACVV Griekwastad (PF046)','PF046','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(46,'2026-05-01','ACVV Beaufort-Wes (PF047)','PF047','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(47,'2026-05-01','ACVV Hoofbestuur (PF048)','PF048','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(48,'2026-05-01','ACVV Pofadder Huis Sophia (PF049)','PF049','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(49,'2026-05-01','ACVV Strand Huis Jan Swart (PF051)','PF051','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(50,'2026-05-01','ACVV Postmasburg Huis Jan Vorster (PF052)','PF052','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(51,'2026-05-01','ACVV Tak Kaapstad (PF053)','PF053','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(52,'2026-05-01','ACVV Kimberley (PF054)','PF054','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(53,'2026-05-01','ACVV Kimberley Speelgoedland (PF055)','PF055','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(54,'2026-05-01','ACVV Koeberg (PF056)','PF056','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(55,'2026-05-01','ACVV Prins Albert Huis Kweekvallei (PF057)','PF057','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(56,'2026-05-01','ACVV Kuruman (PF058)','PF058','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(57,'2026-05-01','ACVV La Belle ACVV Dienstak (PF059)','PF059','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(58,'2026-05-01','ACVV L\'Amour Martinelle Creche (PF060)','PF060','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(59,'2026-05-01','ACVV Magnolia ACVV Dienstak (PF062)','PF062','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(60,'2026-05-01','ACVV Huis Malan Jacobs ACVV Tehuis vir Bejaardes (PF063)','PF063','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(61,'2026-05-01','ACVV Malmesbury (PF064)','PF064','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(62,'2026-05-01','ACVV Somerset Wes Huis Marie Louw (PF065)','PF065','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(63,'2026-05-01','ACVV Ceres Huis Maudie Kriel (PF066)','PF066','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(64,'2026-05-01','ACVV Middelburg Oos-Kaap (PF067)','PF067','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(65,'2026-05-01','ACVV Kuruman Mimosahof (PF068)','PF068','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(66,'2026-05-01','ACVV Mitchells Plain (PF069)','PF069','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(67,'2026-05-01','ACVV Montagu (PF070)','PF070','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(68,'2026-05-01','ACVV Moorreesburg (PF071)','PF071','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(69,'2026-05-01','ACVV Moreson ACVV Kinder- en Jeugsorgsentrum (PF072)','PF072','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(70,'2026-05-01','ACVV Mosselbaai (PF073)','PF073','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(71,'2026-05-01','ACVV Springbok Huis Namakwaland (PF074)','PF074','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(72,'2026-05-01','ACVV Despatch Huis Najaar (PF075)','PF075','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(73,'2026-05-01','ACVV Porterville Tak Huis Nerina (PF076)','PF076','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(74,'2026-05-01','ACVV Dordrecht (PF077)','PF077','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(75,'2026-05-01','ACVV Worcester (PF078)','PF078','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(76,'2026-05-01','ACVV Paarl Vallei Oase Dienssentrum (PF079)','PF079','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(77,'2026-05-01','ACVV Kimberley Ons Huis (PF080)','PF080','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(78,'2026-05-01','ACVV Ons Tuiste ACVV Dienstak (PF081)','PF081','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(79,'2026-05-01','ACVV Op die Kruin ACVV Dienstak (PF082)','PF082','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(80,'2026-05-01','ACVV Upington Oranjehof Tehuis (PF083)','PF083','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(81,'2026-05-01','ACVV Upington Oranjehof Dienssentrum (PF084)','PF084','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(82,'2026-05-01','ACVV Oudtshoorn (PF085)','PF085','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(83,'2026-05-01','ACVV Paarl (PF086)','PF086','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(84,'2026-05-01','ACVV Noorder-Paal (PF087)','PF087','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(85,'2026-05-01','ACVV Paarl Vallei (PF088)','PF088','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(86,'2026-05-01','ACVV Newton Park PE (PF089)','PF089','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(87,'2026-05-01','ACVV PE Noord (PF090)','PF090','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(88,'2026-05-01','ACVV Port Elizabeth Suid (PF092)','PF092','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(89,'2026-05-01','ACVV Port Elizabeth Wes (PF093)','PF093','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(90,'2026-05-01','ACVV Piketberg (PF094)','PF094','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(91,'2026-05-01','ACVV St Helenabaai (PF095)','PF095','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(92,'2026-05-01','ACVV Poplarlaan PE (PF096)','PF096','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(93,'2026-05-01','ACVV Porterville Tak (PF097)','PF097','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(94,'2026-05-01','ACVV Postmasburg (PF098)','PF098','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(95,'2026-05-01','ACVV Prieska (PF099)','PF099','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(96,'2026-05-01','ACVV Caledon Protea Dienssentrum (PF100)','PF100','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(97,'2026-05-01','ACVV Riebeek Kasteel (PF101)','PF101','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(98,'2026-05-01','ACVV Riversdal (PF102)','PF102','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(99,'2026-05-01','ACVV Robertson Huis Le Roux (PF103)','PF103','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(100,'2026-05-01','ACVV Robertson (PF104)','PF104','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(101,'2026-05-01','ACVV Rusoord Tehuis vir Oues van Dae Paarl (PF105)','PF105','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(102,'2026-05-01','ACVV Clanwilliam (PF106)','PF106','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(103,'2026-05-01','ACVV Somerset Oos Huis Silwerjare (PF107)','PF107','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(104,'2026-05-01','ACVV Wellington Tak Silwerkruin (PF108)','PF108','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(105,'2026-05-01','ACVV Wellington Tak Silwerkruin (PF109)','PF109','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(106,'2026-05-01','ACVV Elizabeth Roos Tehuis Dienstak (PF110)','PF110','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(107,'2026-05-01','ACVV Skiereiland Beheerkomitee van die ACVV Dienstak (PF111)','PF111','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(108,'2026-05-01','ACVV Strand Soeterus Tehuis (PF112)','PF112','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(109,'2026-05-01','ACVV Lambersbaai Somerkoelte Tehuis (PF113)','PF113','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(110,'2026-05-01','ACVV Somerset Oos','PF114','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(111,'2026-05-01','ACVV Somerset Wes (PF115)','PF115','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(112,'2026-05-01','ACVV Somerset Oos Dienssentrum (PF116)','PF116','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(113,'2026-05-01','ACVV De Aar Sonder Sorge Tehuis (PF117)','PF117','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(114,'2026-05-01','ACVV Calvinia (PF118)','PF118','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(115,'2026-05-01','ACVV Malmesbury Speelkasteel Creche (PF119)','PF119','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(116,'2026-05-01','ACVV Strand Speelkasteel (PF120)','PF120','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(117,'2026-05-01','ACVV Douglas (PF121)','PF121','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(118,'2026-05-01','ACVV Springbok (PF122)','PF122','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(119,'2026-05-01','ACVV Stellenbosch (PF123)','PF123','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(120,'2026-05-01','ACVV Worcester Stilwaters Dienssentrum (PF124)','PF124','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(121,'2026-05-01','ACVV Die Afrikaanse Christelike Vrouevereniging Strand (PF125)','PF125','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(122,'2026-05-01','ACVV Bredasdorp Suideroord Tehuis (PF126)','PF126','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(123,'2026-05-01','ACVV Swellendam (PF127)','PF127','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(124,'2026-05-01','ACVV Kom Nader Dienssentrum Swellendam (PF128)','PF128','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(125,'2026-05-01','ACVV Touwsrivier (PF129)','PF129','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(126,'2026-05-01','ACVV Middelburg Oos Kaap Huis Karee (PF130)','PF130','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(127,'2026-05-01','ACVV Upington (PF131)','PF131','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(128,'2026-05-01','ACVV Utopia ACVV Tehuis vir Bejaardes Dienstak (PF132)','PF132','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(129,'2026-05-01','ACVV Kirkwood Valleihof Tehuis (PF133)','PF133','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(130,'2026-05-01','ACVV Graaff-Reinet Huis van de Graaff Tehuis (PF134)','PF134','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(131,'2026-05-01','ACVV Huis Van Niekerk Benadehof ACVV Dienssentrum Dienstak (PF135)','PF135','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(132,'2026-05-01','ACVV Huis Vergenoegd Dienstak Diens en Dag (Paarl) (PF136)','PF136','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(133,'2026-05-01','ACVV Huis Vergenoegd Dienstak Siekeboeg (Paarl) (PF137)','PF137','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(134,'2026-05-01','ACVV Huis Vergenoegd Dienstak Woonstelle (Paarl) (PF138)','PF138','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(135,'2026-05-01','ACVV Wellington Tak (PF139)','PF139','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(136,'2026-05-01','ACVV Wellington Tak Fyngoud Dienssentrum (PF140)','PF140','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(137,'2026-05-01','ACVV Paarl Vallei Wielie Walie Creche (PF141)','PF141','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(138,'2026-05-01','ACVV Weskusnessie Dienstak (PF142)','PF142','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(139,'2026-05-01','ACVV Danielskuil (PF143)','PF143','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(140,'2026-05-01','ACVV Victoria Wes Wiekie Wessie Creche (PF144)','PF144','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(141,'2026-05-01','ACVV Worcester (PF145)','PF145','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(142,'2026-05-01','ACVV Ysterplaat Dienstak van die ACVV (PF146)','PF146','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(143,'2026-05-01','ACVV Zonnebloem ACVV Dienstak (PF147)','PF147','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(144,'2026-05-01','ACVV Strand Dienssentrum vir Seniors (PF148)','PF148','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(145,'2026-05-01','ACVV Grabouw Appelkontrei Dienssentrum (PF149)','PF149','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(146,'2026-05-01','ACVV Reivilo Dienssentrum (PF150)','PF150','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(147,'2026-05-01','ACVV Elandsbaai (PF151)','PF151','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(148,'2026-05-01','ACVV Colesberg Old Age Home (PF155)','PF155','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(149,'2026-05-01','ACVV Triomf Child Care Centre (PF156)','PF156','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(150,'2026-05-01','ACVV Barrydale (PF157)','PF157','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(151,'2026-05-01','ACVV Carnarvon Karavaantjie Kleuterskool (PF159)','PF159','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(152,'2026-05-01','ACVV Carnarvon Marcia Louw Kleuterskool (PF160)','PF160','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(153,'2026-05-01','ACVV Malmesbury Dienssentrum (PF161)','PF161','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(154,'2026-05-01','ACVV Malmesbury Naskool (PF162)','PF162','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(155,'2026-05-01','ACVV Somerset Wes Tinktinkie (PF163)','PF163','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(156,'2026-05-01','ACVV Somerset Wes Versorgingsoord Heidi (PF164)','PF164','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(157,'2026-05-01','ACVV Despatch (PF165)','PF165','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(158,'2026-05-01','ACVV Kuruman Heuwelsig (PF166)','PF166','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(159,'2026-05-01','ACVV Oudtshoorn Emmanuel Verpleegskool (PF167)','PF167','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(160,'2026-05-01','ACVV Port Elizabeth Sentraal Khayalethu Jeugsentrum (PF168)','PF168','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(161,'2026-05-01','ACVV Piketberg Trippe Trappe (PF169)','PF169','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(162,'2026-05-01','ACVV Poplarlaan PE Pikkewyntjie (PF170)','PF170','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(163,'2026-05-01','ACVV Robertson Jakaranda Dienssentrum (PF171)','PF171','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(164,'2026-05-01','ACVV Worcester Bollieland Creche (PF172)','PF172','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:39',NULL),(165,'2026-05-01','ACVV Moorreesburg Kleuterland (PF173)','PF173','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:40',NULL),(166,'2026-05-01','ACVV Moorreesburg (PF174)','PF174','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:40',NULL),(167,'2026-05-01','ACVV Dienssentrum Moorreesburg (PF175)','PF175','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:40',NULL),(168,'2026-05-01','ACVV Moorreesburg Heuwelsig (PF176)','PF176','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:40',NULL),(169,'2026-05-01','ACVV Klein Moorrees Moorreesburg (PF177)','PF177','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:40',NULL),(170,'2026-05-01','ACVV Chrisbahof Moorreesburg (PF178)','PF178','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:40',NULL),(171,'2026-05-01','ACVV Irispark (PF179)','PF179','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:40',NULL),(172,'2026-05-01','ACVV Marinerylaan (PF180)','PF180','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:40',NULL),(173,'2026-05-01','ACVV Dysselsdorp Swartberg Dienssentrum (PF181)','PF181','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:40',NULL),(174,'2026-05-01','ACVV Dysselsdorp Siembamba Creche (PF182)','PF182','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:40',NULL),(175,'2026-05-01','ACVV Yzerfontein','PF183','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:40',NULL),(176,'2026-05-01','ACVV Dysselsdorp Shelter (PF184)','PF184','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:40',NULL),(177,'2026-05-01','ACVV Riebeek Wes Humanitas (PF185)','PF185','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:40',NULL),(178,'2026-05-01','ACVV Port Elizabeth Sentraal (PF186)','PF186','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:40',NULL),(179,'2026-05-01','ACVV New Branch Placeholder','PFXXX','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:40',NULL),(180,'2026-01-01','ACVV Aberdeen (PF001)','PF001','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(181,'2026-01-01','ACVV Uitenhage ACVV Dienstak (PF002)','PF002','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(182,'2026-01-01','ACVV Malmesbury Aandskemering (PF003)','PF003','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(183,'2026-01-01','ACVV Piketberg Huis AJ Liebenberg (PF004)','PF004','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(184,'2026-01-01','ACVV Algoapark (PF005)','PF005','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(185,'2026-01-01','ACVV Williston (PF006)','PF006','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(186,'2026-01-01','ACVV Azaleahof ACVV Dienssentrum Dienstak (PF007)','PF007','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(187,'2026-01-01','ACVV Olifantshoek Bergen Rus (PF008)','PF008','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(188,'2026-01-01','ACVV Riebeek Wes Huis Bergsig (PF009)','PF009','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(189,'2026-01-01','ACVV Bothasig Creche Dienstak (PF010)','PF010','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(190,'2026-01-01','ACVV Bredasdorp (PF011)','PF011','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(191,'2026-01-01','ACVV Bredasdorp Suidpunt Diens (PF012)','PF012','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(192,'2026-01-01','ACVV Bright Lights (PF013)1705092.014','PF013','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(193,'2026-01-01','ACVV Caledon (PF014)','PF014','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(194,'2026-01-01','ACVV','PF015','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(195,'2026-01-01','ACVV Carnarvon (PF017)','PF017','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(196,'2026-01-01','ACVV Ceres (PF018)','PF018','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(197,'2026-01-01','ACVV Adelaide (PF019)','PF019','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(198,'2026-01-01','ACVV Cradock (PF020)','PF020','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(199,'2026-01-01','ACVV Britstown (PF021)','PF021','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(200,'2026-01-01','ACVV Carnarvon Huis Danie van Huyssteen (PF022)','PF022','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(201,'2026-01-01','ACVV De Aar (PF023)','PF023','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(202,'2026-01-01','ACVV De Aar Lollapot (PF023B)','PF023B','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(203,'2026-01-01','ACVV De Grendel ACVV Dienstak (PF024)','PF024','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(204,'2026-01-01','ACVV Delft Dienstak (PF025)','PF025','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(205,'2026-01-01','ACVV Despatch Dienssentrum (PF026)','PF026','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(206,'2026-01-01','ACVV Alexandria (PF027)','PF027','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(207,'2026-01-01','ACVV Tulbagh (PF028)','PF028','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(208,'2026-01-01','ACVV Richmond Driefontein Dienssentrum (PF030)','PF030','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(209,'2026-01-01','ACVV Dysselsdorp (PF031)','PF031','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(210,'2026-01-01','ACVV Edelweiss ACVV Dienssentrum en Wooneenhede Dienstak (PF032)','PF032','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(211,'2026-01-01','ACVV Eldorado Dienstak (PF033)','PF033','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(212,'2026-01-01','ACVV Cradock Elizabeth Jordaan (PF034)','PF034','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(213,'2026-01-01','ACVV Franschhoek Fleur de Lis (PF035)','PF035','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(214,'2026-01-01','ACVV Franschhoek (PF036)','PF036','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(215,'2026-01-01','ACVV Victoria Wes (PF037)','PF037','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(216,'2026-01-01','ACVV Port Elizabeth Wes Huis Genot (PF038)','PF038','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(217,'2026-01-01','ACVV George (PF039)','PF039','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(218,'2026-01-01','ACVV Grabouw (PF040)','PF040','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(219,'2026-01-01','ACVV Grabouw Huis Groenland (PF041)','PF041','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(220,'2026-01-01','ACVV Grahamstad (PF042)','PF042','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(221,'2026-01-01','ACVV Newton Park PE Haas Das Creche (PF043)','PF043','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(222,'2026-01-01','ACVV Caledon Heidehof (PF044)','PF044','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(223,'2026-01-01','ACVV Heidelberg (PF045)','PF045','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(224,'2026-01-01','ACVV Griekwastad (PF046)','PF046','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(225,'2026-01-01','ACVV Beaufort-Wes (PF047)','PF047','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(226,'2026-01-01','ACVV Hoofbestuur (PF048)','PF048','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(227,'2026-01-01','ACVV Pofadder Huis Sophia (PF049)','PF049','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(228,'2026-01-01','ACVV Strand Huis Jan Swart (PF051)','PF051','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(229,'2026-01-01','ACVV Postmasburg Huis Jan Vorster (PF052)','PF052','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(230,'2026-01-01','ACVV Tak Kaapstad (PF053)','PF053','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(231,'2026-01-01','ACVV Kimberley (PF054)','PF054','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(232,'2026-01-01','ACVV Kimberley Speelgoedland (PF055)','PF055','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(233,'2026-01-01','ACVV Koeberg (PF056)','PF056','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(234,'2026-01-01','ACVV Prins Albert Huis Kweekvallei (PF057)','PF057','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(235,'2026-01-01','ACVV Kuruman (PF058)','PF058','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(236,'2026-01-01','ACVV La Belle ACVV Dienstak (PF059)','PF059','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(237,'2026-01-01','ACVV L\'Amour Martinelle Creche (PF060)','PF060','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(238,'2026-01-01','ACVV Magnolia ACVV Dienstak (PF062)','PF062','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(239,'2026-01-01','ACVV Huis Malan Jacobs ACVV Tehuis vir Bejaardes (PF063)','PF063','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(240,'2026-01-01','ACVV Malmesbury (PF064)','PF064','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(241,'2026-01-01','ACVV Somerset Wes Huis Marie Louw (PF065)','PF065','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(242,'2026-01-01','ACVV Ceres Huis Maudie Kriel (PF066)','PF066','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(243,'2026-01-01','ACVV Middelburg Oos-Kaap (PF067)','PF067','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(244,'2026-01-01','ACVV Kuruman Mimosahof (PF068)','PF068','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(245,'2026-01-01','ACVV Mitchells Plain (PF069)','PF069','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(246,'2026-01-01','ACVV Montagu (PF070)','PF070','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(247,'2026-01-01','ACVV Moorreesburg (PF071)','PF071','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(248,'2026-01-01','ACVV Moreson ACVV Kinder- en Jeugsorgsentrum (PF072)','PF072','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(249,'2026-01-01','ACVV Mosselbaai (PF073)','PF073','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(250,'2026-01-01','ACVV Springbok Huis Namakwaland (PF074)','PF074','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(251,'2026-01-01','ACVV Despatch Huis Najaar (PF075)','PF075','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(252,'2026-01-01','ACVV Porterville Tak Huis Nerina (PF076)','PF076','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(253,'2026-01-01','ACVV Dordrecht (PF077)','PF077','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(254,'2026-01-01','ACVV Worcester (PF078)','PF078','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(255,'2026-01-01','ACVV Paarl Vallei Oase Dienssentrum (PF079)','PF079','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(256,'2026-01-01','ACVV Kimberley Ons Huis (PF080)','PF080','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(257,'2026-01-01','ACVV Ons Tuiste ACVV Dienstak (PF081)','PF081','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(258,'2026-01-01','ACVV Op die Kruin ACVV Dienstak (PF082)','PF082','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(259,'2026-01-01','ACVV Upington Oranjehof Tehuis (PF083)','PF083','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(260,'2026-01-01','ACVV Upington Oranjehof Dienssentrum (PF084)','PF084','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(261,'2026-01-01','ACVV Oudtshoorn (PF085)','PF085','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(262,'2026-01-01','ACVV Paarl (PF086)','PF086','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(263,'2026-01-01','ACVV Noorder-Paal (PF087)','PF087','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(264,'2026-01-01','ACVV Paarl Vallei (PF088)','PF088','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(265,'2026-01-01','ACVV Newton Park PE (PF089)','PF089','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(266,'2026-01-01','ACVV PE Noord (PF090)','PF090','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(267,'2026-01-01','ACVV Port Elizabeth Suid (PF092)','PF092','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(268,'2026-01-01','ACVV Port Elizabeth Wes (PF093)','PF093','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(269,'2026-01-01','ACVV Piketberg (PF094)','PF094','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(270,'2026-01-01','ACVV St Helenabaai (PF095)','PF095','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(271,'2026-01-01','ACVV Poplarlaan PE (PF096)','PF096','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(272,'2026-01-01','ACVV Porterville Tak (PF097)','PF097','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(273,'2026-01-01','ACVV Postmasburg (PF098)','PF098','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(274,'2026-01-01','ACVV Prieska (PF099)','PF099','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(275,'2026-01-01','ACVV Caledon Protea Dienssentrum (PF100)','PF100','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(276,'2026-01-01','ACVV Riebeek Kasteel (PF101)','PF101','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(277,'2026-01-01','ACVV Riversdal (PF102)','PF102','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(278,'2026-01-01','ACVV Robertson Huis Le Roux (PF103)','PF103','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(279,'2026-01-01','ACVV Robertson (PF104)','PF104','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(280,'2026-01-01','ACVV Rusoord Tehuis vir Oues van Dae Paarl (PF105)','PF105','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(281,'2026-01-01','ACVV Clanwilliam (PF106)','PF106','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(282,'2026-01-01','ACVV Somerset Oos Huis Silwerjare (PF107)','PF107','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(283,'2026-01-01','ACVV Wellington Tak Silwerkruin (PF108)','PF108','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(284,'2026-01-01','ACVV Wellington Tak Silwerkruin (PF109)','PF109','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(285,'2026-01-01','ACVV Elizabeth Roos Tehuis Dienstak (PF110)','PF110','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(286,'2026-01-01','ACVV Skiereiland Beheerkomitee van die ACVV Dienstak (PF111)','PF111','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(287,'2026-01-01','ACVV Strand Soeterus Tehuis (PF112)','PF112','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(288,'2026-01-01','ACVV Lambersbaai Somerkoelte Tehuis (PF113)','PF113','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(289,'2026-01-01','ACVV Somerset Oos','PF114','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(290,'2026-01-01','ACVV Somerset Wes (PF115)','PF115','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(291,'2026-01-01','ACVV Somerset Oos Dienssentrum (PF116)','PF116','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(292,'2026-01-01','ACVV De Aar Sonder Sorge Tehuis (PF117)','PF117','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(293,'2026-01-01','ACVV Calvinia (PF118)','PF118','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(294,'2026-01-01','ACVV Malmesbury Speelkasteel Creche (PF119)','PF119','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(295,'2026-01-01','ACVV Strand Speelkasteel (PF120)','PF120','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(296,'2026-01-01','ACVV Douglas (PF121)','PF121','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(297,'2026-01-01','ACVV Springbok (PF122)','PF122','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(298,'2026-01-01','ACVV Stellenbosch (PF123)','PF123','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(299,'2026-01-01','ACVV Worcester Stilwaters Dienssentrum (PF124)','PF124','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(300,'2026-01-01','ACVV Die Afrikaanse Christelike Vrouevereniging Strand (PF125)','PF125','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(301,'2026-01-01','ACVV Bredasdorp Suideroord Tehuis (PF126)','PF126','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:49',NULL),(302,'2026-01-01','ACVV Swellendam (PF127)','PF127','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(303,'2026-01-01','ACVV Kom Nader Dienssentrum Swellendam (PF128)','PF128','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(304,'2026-01-01','ACVV Touwsrivier (PF129)','PF129','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(305,'2026-01-01','ACVV Middelburg Oos Kaap Huis Karee (PF130)','PF130','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(306,'2026-01-01','ACVV Upington (PF131)','PF131','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(307,'2026-01-01','ACVV Utopia ACVV Tehuis vir Bejaardes Dienstak (PF132)','PF132','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(308,'2026-01-01','ACVV Kirkwood Valleihof Tehuis (PF133)','PF133','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(309,'2026-01-01','ACVV Graaff-Reinet Huis van de Graaff Tehuis (PF134)','PF134','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(310,'2026-01-01','ACVV Huis Van Niekerk Benadehof ACVV Dienssentrum Dienstak (PF135)','PF135','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(311,'2026-01-01','ACVV Huis Vergenoegd Dienstak Diens en Dag (Paarl) (PF136)','PF136','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(312,'2026-01-01','ACVV Huis Vergenoegd Dienstak Siekeboeg (Paarl) (PF137)','PF137','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(313,'2026-01-01','ACVV Huis Vergenoegd Dienstak Woonstelle (Paarl) (PF138)','PF138','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(314,'2026-01-01','ACVV Wellington Tak (PF139)','PF139','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(315,'2026-01-01','ACVV Wellington Tak Fyngoud Dienssentrum (PF140)','PF140','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(316,'2026-01-01','ACVV Paarl Vallei Wielie Walie Creche (PF141)','PF141','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(317,'2026-01-01','ACVV Weskusnessie Dienstak (PF142)','PF142','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(318,'2026-01-01','ACVV Danielskuil (PF143)','PF143','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(319,'2026-01-01','ACVV Victoria Wes Wiekie Wessie Creche (PF144)','PF144','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(320,'2026-01-01','ACVV Worcester (PF145)','PF145','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(321,'2026-01-01','ACVV Ysterplaat Dienstak van die ACVV (PF146)','PF146','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(322,'2026-01-01','ACVV Zonnebloem ACVV Dienstak (PF147)','PF147','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(323,'2026-01-01','ACVV Strand Dienssentrum vir Seniors (PF148)','PF148','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(324,'2026-01-01','ACVV Grabouw Appelkontrei Dienssentrum (PF149)','PF149','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(325,'2026-01-01','ACVV Reivilo Dienssentrum (PF150)','PF150','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(326,'2026-01-01','ACVV Elandsbaai (PF151)','PF151','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(327,'2026-01-01','ACVV Colesberg Old Age Home (PF155)','PF155','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(328,'2026-01-01','ACVV Triomf Child Care Centre (PF156)','PF156','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(329,'2026-01-01','ACVV Barrydale (PF157)','PF157','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(330,'2026-01-01','ACVV Carnarvon Karavaantjie Kleuterskool (PF159)','PF159','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(331,'2026-01-01','ACVV Carnarvon Marcia Louw Kleuterskool (PF160)','PF160','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(332,'2026-01-01','ACVV Malmesbury Dienssentrum (PF161)','PF161','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(333,'2026-01-01','ACVV Malmesbury Naskool (PF162)','PF162','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(334,'2026-01-01','ACVV Somerset Wes Tinktinkie (PF163)','PF163','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(335,'2026-01-01','ACVV Somerset Wes Versorgingsoord Heidi (PF164)','PF164','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(336,'2026-01-01','ACVV Despatch (PF165)','PF165','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(337,'2026-01-01','ACVV Kuruman Heuwelsig (PF166)','PF166','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(338,'2026-01-01','ACVV Oudtshoorn Emmanuel Verpleegskool (PF167)','PF167','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(339,'2026-01-01','ACVV Port Elizabeth Sentraal Khayalethu Jeugsentrum (PF168)','PF168','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(340,'2026-01-01','ACVV Piketberg Trippe Trappe (PF169)','PF169','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(341,'2026-01-01','ACVV Poplarlaan PE Pikkewyntjie (PF170)','PF170','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(342,'2026-01-01','ACVV Robertson Jakaranda Dienssentrum (PF171)','PF171','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(343,'2026-01-01','ACVV Worcester Bollieland Creche (PF172)','PF172','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(344,'2026-01-01','ACVV Moorreesburg Kleuterland (PF173)','PF173','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(345,'2026-01-01','ACVV Moorreesburg (PF174)','PF174','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(346,'2026-01-01','ACVV Dienssentrum Moorreesburg (PF175)','PF175','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(347,'2026-01-01','ACVV Moorreesburg Heuwelsig (PF176)','PF176','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(348,'2026-01-01','ACVV Klein Moorrees Moorreesburg (PF177)','PF177','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(349,'2026-01-01','ACVV Chrisbahof Moorreesburg (PF178)','PF178','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(350,'2026-01-01','ACVV Irispark (PF179)','PF179','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(351,'2026-01-01','ACVV Marinerylaan (PF180)','PF180','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(352,'2026-01-01','ACVV Dysselsdorp Swartberg Dienssentrum (PF181)','PF181','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(353,'2026-01-01','ACVV Dysselsdorp Siembamba Creche (PF182)','PF182','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(354,'2026-01-01','ACVV Yzerfontein','PF183','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(355,'2026-01-01','ACVV Dysselsdorp Shelter (PF184)','PF184','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(356,'2026-01-01','ACVV Riebeek Wes Humanitas (PF185)','PF185','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(357,'2026-01-01','ACVV Port Elizabeth Sentraal (PF186)','PF186','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL),(358,'2026-01-01','ACVV New Branch Placeholder','PFXXX','Active','Debit Order',NULL,NULL,0,0.00,0.00,'Unreconciled',NULL,NULL,NULL,NULL,NULL,0,NULL,'2026-06-04 19:13:50',NULL);
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

-- Dump completed on 2026-06-04 21:22:06
