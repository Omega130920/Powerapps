-- MySQL dump 10.13  Distrib 8.0.43, for Win64 (x86_64)
--
-- Host: localhost    Database: crm_unity
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
-- Table structure for table `account_emailaddress`
--

DROP TABLE IF EXISTS `account_emailaddress`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `account_emailaddress` (
  `id` int NOT NULL AUTO_INCREMENT,
  `email` varchar(254) NOT NULL,
  `verified` tinyint(1) NOT NULL,
  `primary` tinyint(1) NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `account_emailaddress_user_id_email_987c8728_uniq` (`user_id`,`email`),
  KEY `account_emailaddress_email_03be32b2` (`email`),
  CONSTRAINT `account_emailaddress_user_id_2c513194_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `account_emailconfirmation`
--

DROP TABLE IF EXISTS `account_emailconfirmation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `account_emailconfirmation` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created` datetime(6) NOT NULL,
  `sent` datetime(6) DEFAULT NULL,
  `key` varchar(64) NOT NULL,
  `email_address_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `key` (`key`),
  KEY `account_emailconfirm_email_address_id_5b7f8c58_fk_account_e` (`email_address_id`),
  CONSTRAINT `account_emailconfirm_email_address_id_5b7f8c58_fk_account_e` FOREIGN KEY (`email_address_id`) REFERENCES `account_emailaddress` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

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
) ENGINE=InnoDB AUTO_INCREMENT=173 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

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
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

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
-- Table structure for table `bank_line_notes`
--

DROP TABLE IF EXISTS `bank_line_notes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bank_line_notes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `recon_record_id` int NOT NULL,
  `note_text` text NOT NULL,
  `category` varchar(100) DEFAULT NULL,
  `created_by` varchar(150) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_bank_line_notes_recon` (`recon_record_id`),
  CONSTRAINT `fk_bank_line_notes_recon` FOREIGN KEY (`recon_record_id`) REFERENCES `reconned_bank` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `bill_settlement`
--

DROP TABLE IF EXISTS `bill_settlement`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bill_settlement` (
  `id` int NOT NULL AUTO_INCREMENT,
  `reconned_bank_line_id` int DEFAULT NULL,
  `original_import_bank_id` int DEFAULT NULL,
  `unity_bill_source_id` int NOT NULL,
  `settlement_date` datetime(6) NOT NULL,
  `settled_amount` decimal(15,2) NOT NULL,
  `settlement_note` text,
  `source_credit_note_id` int DEFAULT NULL,
  `source_journal_entry_id` int DEFAULT NULL,
  `confirmed_by_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_settle_recon` (`reconned_bank_line_id`),
  KEY `fk_settle_bill` (`unity_bill_source_id`),
  CONSTRAINT `fk_settle_bill` FOREIGN KEY (`unity_bill_source_id`) REFERENCES `unity_bill` (`id`),
  CONSTRAINT `fk_settle_recon` FOREIGN KEY (`reconned_bank_line_id`) REFERENCES `reconned_bank` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=38 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cbc`
--

DROP TABLE IF EXISTS `cbc`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cbc` (
  `Member_Group_Code` varchar(255) DEFAULT NULL,
  `Title` varchar(255) DEFAULT NULL,
  `First_Name` varchar(255) DEFAULT NULL,
  `Surname` varchar(255) DEFAULT NULL,
  `ID_Number` varchar(255) DEFAULT NULL,
  `Email_Address` varchar(255) DEFAULT NULL,
  `Indemnity` varchar(225) DEFAULT NULL,
  `Work_Dial_Code` varchar(10) DEFAULT NULL,
  `Work_Contact_Number` varchar(255) DEFAULT NULL,
  `Fax_Dial_Code` varchar(10) DEFAULT NULL,
  `Fax_Number` varchar(255) DEFAULT NULL,
  `Mobile_Number` varchar(255) DEFAULT NULL,
  `Business_Postal_address` varchar(255) DEFAULT NULL,
  `Post_Code` varchar(10) DEFAULT NULL,
  `Business_Physical_address` varchar(255) DEFAULT NULL,
  `Post_Code2` varchar(10) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cbc_admin_person`
--

DROP TABLE IF EXISTS `cbc_admin_person`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cbc_admin_person` (
  `Member_Group_Code` varchar(255) DEFAULT NULL,
  `Title` varchar(255) DEFAULT NULL,
  `First_Name` varchar(255) DEFAULT NULL,
  `Surname` varchar(255) DEFAULT NULL,
  `ID_Number` varchar(255) DEFAULT NULL,
  `Email_Address` varchar(255) DEFAULT NULL,
  `Work_Dial_Code` varchar(10) DEFAULT NULL,
  `Work_Contact_Number` varchar(255) DEFAULT NULL,
  `Fax_Dial_Code` varchar(10) DEFAULT NULL,
  `Fax_Number` varchar(255) DEFAULT NULL,
  `Mobile_Number` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cbc_consultancy_person`
--

DROP TABLE IF EXISTS `cbc_consultancy_person`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cbc_consultancy_person` (
  `Member_Group_Code` varchar(255) DEFAULT NULL,
  `Title` varchar(255) DEFAULT NULL,
  `First_Name` varchar(255) DEFAULT NULL,
  `Surname` varchar(255) DEFAULT NULL,
  `ID_Number` varchar(255) DEFAULT NULL,
  `Email_Address` varchar(255) DEFAULT NULL,
  `Work_Dial_Code` varchar(10) DEFAULT NULL,
  `Work_Contact_Number` varchar(255) DEFAULT NULL,
  `Fax_Dial_Code` varchar(10) DEFAULT NULL,
  `Fax_Number` varchar(255) DEFAULT NULL,
  `Mobile_Number` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cfa`
--

DROP TABLE IF EXISTS `cfa`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cfa` (
  `Member_Group_Code` varchar(255) DEFAULT NULL,
  `Title` varchar(255) DEFAULT NULL,
  `First_Name` varchar(255) DEFAULT NULL,
  `Surname` varchar(255) DEFAULT NULL,
  `ID_Number` varchar(255) DEFAULT NULL,
  `Email_Address` varchar(255) DEFAULT NULL,
  `Work_Dial_Code` varchar(10) DEFAULT NULL,
  `Work_Contact_Number` varchar(255) DEFAULT NULL,
  `Fax_Dial_Code` varchar(10) DEFAULT NULL,
  `Fax_Number` varchar(255) DEFAULT NULL,
  `Mobile_Number` varchar(255) DEFAULT NULL,
  `Business_Postal_address` varchar(255) DEFAULT NULL,
  `Post_Code` varchar(10) DEFAULT NULL,
  `Business_Physical_address` varchar(255) DEFAULT NULL,
  `Post_Code2` varchar(10) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cfa2`
--

DROP TABLE IF EXISTS `cfa2`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cfa2` (
  `Member_Group_Code` varchar(255) DEFAULT NULL,
  `Title` varchar(255) DEFAULT NULL,
  `First_Name` varchar(255) DEFAULT NULL,
  `Surname` varchar(255) DEFAULT NULL,
  `ID_Number` varchar(255) DEFAULT NULL,
  `Email_Address` varchar(255) DEFAULT NULL,
  `Work_Dial_Code` varchar(10) DEFAULT NULL,
  `Work_Contact_Number` varchar(255) DEFAULT NULL,
  `Fax_Dial_Code` varchar(10) DEFAULT NULL,
  `Fax_Number` varchar(255) DEFAULT NULL,
  `Mobile_Number` varchar(255) DEFAULT NULL,
  `Business_Postal_address` varchar(255) DEFAULT NULL,
  `Post_Code` varchar(10) DEFAULT NULL,
  `Business_Physical_address` varchar(255) DEFAULT NULL,
  `Post_Code2` varchar(10) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cfa3`
--

DROP TABLE IF EXISTS `cfa3`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cfa3` (
  `Member_Group_Code` varchar(255) DEFAULT NULL,
  `Title` varchar(255) DEFAULT NULL,
  `First_Name` varchar(255) DEFAULT NULL,
  `Surname` varchar(255) DEFAULT NULL,
  `ID_Number` varchar(255) DEFAULT NULL,
  `Email_Address` varchar(255) DEFAULT NULL,
  `Work_Dial_Code` varchar(10) DEFAULT NULL,
  `Work_Contact_Number` varchar(255) DEFAULT NULL,
  `Fax_Dial_Code` varchar(10) DEFAULT NULL,
  `Fax_Number` varchar(255) DEFAULT NULL,
  `Mobile_Number` varchar(255) DEFAULT NULL,
  `Business_Postal_address` varchar(255) DEFAULT NULL,
  `Post_Code` varchar(10) DEFAULT NULL,
  `Business_Physical_address` varchar(255) DEFAULT NULL,
  `Post_Code2` varchar(10) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cfa_admin_person`
--

DROP TABLE IF EXISTS `cfa_admin_person`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cfa_admin_person` (
  `Member_Group_Code` varchar(255) DEFAULT NULL,
  `Title` varchar(255) DEFAULT NULL,
  `First_Name` varchar(255) DEFAULT NULL,
  `Surname` varchar(255) DEFAULT NULL,
  `ID_Number` varchar(255) DEFAULT NULL,
  `Email_Address` varchar(255) DEFAULT NULL,
  `Work_Dial_Code` varchar(10) DEFAULT NULL,
  `Work_Contact_Number` varchar(255) DEFAULT NULL,
  `Fax_Dial_Code` varchar(10) DEFAULT NULL,
  `Fax_Number` varchar(255) DEFAULT NULL,
  `Mobile_Number` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `client_notes`
--

DROP TABLE IF EXISTS `client_notes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `client_notes` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `Member Group Code` text,
  `date` datetime DEFAULT NULL,
  `User` text,
  `notes` text,
  `Communication_Type` varchar(90) DEFAULT NULL,
  `Action_Notes` varchar(90) DEFAULT NULL,
  `attached_email_id` varchar(255) DEFAULT NULL,
  `attached_file_name` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB AUTO_INCREMENT=56 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `communications_person`
--

DROP TABLE IF EXISTS `communications_person`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `communications_person` (
  `Member_Group_Code` varchar(255) DEFAULT NULL,
  `Title` varchar(255) DEFAULT NULL,
  `First_Name` varchar(255) DEFAULT NULL,
  `Surname` varchar(255) DEFAULT NULL,
  `ID_Number` varchar(255) DEFAULT NULL,
  `Email_Address` varchar(255) DEFAULT NULL,
  `Work_Dial_Code` varchar(10) DEFAULT NULL,
  `Work_Contact_Number` varchar(255) DEFAULT NULL,
  `Fax_Dial_Code` varchar(10) DEFAULT NULL,
  `Fax_Number` varchar(255) DEFAULT NULL,
  `Mobile_Number` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

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
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `credit_note`
--

DROP TABLE IF EXISTS `credit_note`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `credit_note` (
  `id` int NOT NULL AUTO_INCREMENT,
  `ccdates_month` date DEFAULT NULL,
  `fund_code` varchar(50) DEFAULT NULL,
  `member_group_code` varchar(50) NOT NULL,
  `member_group_name` varchar(255) DEFAULT NULL,
  `active_members` int DEFAULT NULL,
  `schedule_date` date DEFAULT NULL,
  `final_data_received_date` date DEFAULT NULL,
  `schedule_amount` decimal(10,2) DEFAULT NULL,
  `confirmation_date` date DEFAULT NULL,
  `bank_stmt_date` date DEFAULT NULL,
  `bank_deposit_amount` decimal(10,2) DEFAULT NULL,
  `allocated_amount` decimal(10,2) DEFAULT NULL,
  `comment` varchar(255) DEFAULT NULL,
  `receipt_in_live` varchar(50) DEFAULT NULL,
  `receipting_done_by` varchar(100) DEFAULT NULL,
  `balance_sufficient_flag` varchar(10) DEFAULT NULL,
  `date_letter_checked` date DEFAULT NULL,
  `done_by` varchar(100) DEFAULT NULL,
  `processed_date` datetime DEFAULT CURRENT_TIMESTAMP,
  `processed_by` varchar(100) DEFAULT NULL,
  `note_selection` varchar(100) DEFAULT NULL,
  `fiscal_date` date DEFAULT NULL,
  `review_note` varchar(500) DEFAULT NULL,
  `assigned_unity_bill_id` int DEFAULT NULL,
  `member_group_id` varchar(255) DEFAULT NULL,
  `authorization_status` varchar(20) DEFAULT 'Idle',
  `requested_amount` decimal(12,2) DEFAULT '0.00',
  `request_reason` text,
  `authorized_by` varchar(100) DEFAULT NULL,
  `authorized_at` datetime DEFAULT NULL,
  `credit_link_status` varchar(20) DEFAULT 'Unlinked',
  `link_request_reason` text,
  `pending_linked_bill_id` int DEFAULT NULL,
  `source_bank_line_id` int DEFAULT NULL,
  `date_identified` date DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_credit_unity_mg` (`member_group_id`),
  KEY `fk_source_bank_line` (`source_bank_line_id`),
  KEY `idx_credit_note_selection` (`note_selection`),
  CONSTRAINT `fk_credit_unity_mg` FOREIGN KEY (`member_group_id`) REFERENCES `internal_mg_list` (`A_Company_Code`) ON DELETE SET NULL,
  CONSTRAINT `fk_source_bank_line` FOREIGN KEY (`source_bank_line_id`) REFERENCES `reconned_bank` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `crm_complaint_log`
--

DROP TABLE IF EXISTS `crm_complaint_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `crm_complaint_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_by_id` int DEFAULT NULL,
  `complainant` varchar(255) NOT NULL,
  `employer` varchar(255) DEFAULT NULL,
  `nature_of_complaint` text NOT NULL,
  `resolution` text,
  `created_date` date DEFAULT NULL,
  `resolved_date` datetime DEFAULT NULL,
  `current_status` varchar(50) DEFAULT 'Open',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `member_number` varchar(100) DEFAULT NULL,
  `id_passport_number` varchar(100) DEFAULT NULL,
  `pfa` varchar(3) DEFAULT 'No',
  `action_taken` text,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `crm_core_memberdocument`
--

DROP TABLE IF EXISTS `crm_core_memberdocument`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `crm_core_memberdocument` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `related_member_group_code` varchar(255) NOT NULL,
  `document_file` varchar(100) NOT NULL,
  `title` varchar(255) DEFAULT NULL,
  `uploaded_by` varchar(150) NOT NULL,
  `uploaded_at` datetime(6) NOT NULL,
  `id_document` varchar(45) DEFAULT NULL,
  `proof_of_address` varchar(45) DEFAULT NULL,
  `bank_statement` varchar(45) DEFAULT NULL,
  `appointment_letter` varchar(45) DEFAULT NULL,
  `vat_number` varchar(45) DEFAULT NULL,
  `mandate_trust_deed` varchar(45) DEFAULT NULL,
  `tax_number` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=37 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `crm_delegate_actions`
--

DROP TABLE IF EXISTS `crm_delegate_actions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `crm_delegate_actions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `task_email_id` varchar(255) NOT NULL,
  `action_type` varchar(50) NOT NULL,
  `action_user` varchar(100) NOT NULL,
  `action_timestamp` datetime DEFAULT CURRENT_TIMESTAMP,
  `note_content` text,
  `related_subject` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `task_email_id` (`task_email_id`)
) ENGINE=InnoDB AUTO_INCREMENT=96 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `crm_delegate_to`
--

DROP TABLE IF EXISTS `crm_delegate_to`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `crm_delegate_to` (
  `id` int NOT NULL AUTO_INCREMENT,
  `email_id` varchar(255) NOT NULL,
  `subject` varchar(512) DEFAULT NULL,
  `sender` varchar(255) DEFAULT NULL,
  `snippet` varchar(512) DEFAULT NULL,
  `received_timestamp` datetime DEFAULT CURRENT_TIMESTAMP,
  `status` varchar(20) DEFAULT 'Delegated',
  `delegated_by` varchar(100) DEFAULT NULL,
  `delegated_to` varchar(100) DEFAULT NULL,
  `work_related` varchar(5) DEFAULT 'Yes',
  `Member_Group_Code` varchar(255) DEFAULT NULL,
  `membership_number` varchar(100) DEFAULT NULL,
  `id_passport` varchar(50) DEFAULT NULL,
  `category` varchar(50) DEFAULT NULL,
  `type` varchar(255) DEFAULT NULL,
  `method` varchar(50) DEFAULT 'Email',
  `delegated_attachments` text,
  `internal_notes` text,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email_id` (`email_id`)
) ENGINE=InnoDB AUTO_INCREMENT=45 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `crm_delegation_report`
--

DROP TABLE IF EXISTS `crm_delegation_report`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `crm_delegation_report` (
  `email_id` varchar(255) NOT NULL,
  `subject` varchar(512) DEFAULT NULL,
  `received_timestamp` datetime DEFAULT NULL,
  `delegated_by` varchar(100) DEFAULT NULL,
  `delegated_to` varchar(100) DEFAULT NULL,
  `DelegationStatus` varchar(20) DEFAULT NULL,
  `work_related` varchar(5) DEFAULT NULL,
  `Member_Group_Code` varchar(255) DEFAULT NULL,
  `EnquiryCategory` varchar(50) DEFAULT NULL,
  `EnquirySelection` varchar(255) DEFAULT NULL,
  `TotalActionsTaken` int NOT NULL DEFAULT '0',
  `IsCompleted` varchar(3) NOT NULL DEFAULT 'No',
  `CompletionTimestamp` datetime DEFAULT NULL,
  PRIMARY KEY (`email_id`),
  KEY `idx_report_delegated_to` (`delegated_to`),
  KEY `idx_report_received_ts` (`received_timestamp`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `crm_direct_email_log`
--

DROP TABLE IF EXISTS `crm_direct_email_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `crm_direct_email_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `member_group_code` varchar(50) NOT NULL,
  `subject` varchar(255) NOT NULL,
  `recipient_email` varchar(255) NOT NULL,
  `body_content` longtext NOT NULL,
  `sent_by_user_id` int DEFAULT NULL,
  `sent_at` datetime NOT NULL,
  `outlook_message_id` varchar(225) DEFAULT NULL,
  `action_type` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `member_group_code` (`member_group_code`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `crm_inbox`
--

DROP TABLE IF EXISTS `crm_inbox`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `crm_inbox` (
  `email_id` varchar(255) NOT NULL,
  `subject` varchar(512) DEFAULT NULL,
  `sender` varchar(255) DEFAULT NULL,
  `snippet` varchar(512) DEFAULT NULL,
  `received_timestamp` datetime DEFAULT CURRENT_TIMESTAMP,
  `status` varchar(20) DEFAULT 'Pending',
  `delegated_by` varchar(100) DEFAULT NULL,
  `delegated_to` varchar(100) DEFAULT NULL,
  `work_related` varchar(5) DEFAULT 'No',
  `Member_Group_Code` varchar(255) DEFAULT NULL,
  `id_passport` varchar(50) DEFAULT NULL,
  `category` varchar(50) DEFAULT NULL,
  `type` varchar(50) DEFAULT NULL,
  `method` varchar(50) DEFAULT 'Email',
  PRIMARY KEY (`email_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `crm_unity_outlooktoken`
--

DROP TABLE IF EXISTS `crm_unity_outlooktoken`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `crm_unity_outlooktoken` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `access_token` longtext NOT NULL,
  `refresh_token` longtext NOT NULL,
  `expires_at` datetime NOT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `fk_outlook_user` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `direct_emails`
--

DROP TABLE IF EXISTS `direct_emails`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `direct_emails` (
  `email_id` int unsigned NOT NULL AUTO_INCREMENT,
  `sender_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Name provided by the sender (optional)',
  `sender_email` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'The email address of the sender',
  `subject` varchar(555) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'The subject line of the message',
  `body` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'The full content of the email/message',
  `is_read` tinyint(1) NOT NULL DEFAULT '0' COMMENT 'Flag to track if the message has been processed or read',
  `received_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'The date and time the message was received',
  PRIMARY KEY (`email_id`),
  KEY `idx_sender_email` (`sender_email`),
  KEY `idx_received_at` (`received_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Stores direct email communications/contact form submissions';
/*!40101 SET character_set_client = @saved_cs_client */;

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
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

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
) ENGINE=InnoDB AUTO_INCREMENT=44 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

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
) ENGINE=InnoDB AUTO_INCREMENT=39 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

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
-- Table structure for table `django_site`
--

DROP TABLE IF EXISTS `django_site`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_site` (
  `id` int NOT NULL AUTO_INCREMENT,
  `domain` varchar(100) NOT NULL,
  `name` varchar(50) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_site_domain_a2e37b91_uniq` (`domain`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `global_fund_contact_list`
--

DROP TABLE IF EXISTS `global_fund_contact_list`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `global_fund_contact_list` (
  `Member_Group_Code` varchar(255) DEFAULT NULL,
  `Member_Group_Name` varchar(255) DEFAULT NULL,
  `Commencement_Date` date DEFAULT NULL,
  `Fund_status` varchar(255) DEFAULT NULL,
  `Business_Postal_Address` varchar(255) DEFAULT NULL,
  `Business_Postal_address_post_Code` varchar(255) DEFAULT NULL,
  `Business_Physical_Address2` varchar(255) DEFAULT NULL,
  `Business_Physical_address_post_code2` varchar(255) DEFAULT NULL,
  `recon_contact_1_name` varchar(255) DEFAULT NULL,
  `recon_contact_1_email` varchar(255) DEFAULT NULL,
  `recon_contact_2_name` varchar(255) DEFAULT NULL,
  `recon_contact_2_email` varchar(255) DEFAULT NULL,
  `fund_status_date` date DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `human_resources`
--

DROP TABLE IF EXISTS `human_resources`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `human_resources` (
  `Member_Group_Code` varchar(255) DEFAULT NULL,
  `Title` varchar(255) DEFAULT NULL,
  `First_Name` varchar(255) DEFAULT NULL,
  `Surname` varchar(255) DEFAULT NULL,
  `ID_Number` varchar(255) DEFAULT NULL,
  `Email_Address` varchar(255) DEFAULT NULL,
  `Indemnity` varchar(225) DEFAULT NULL,
  `Work_Dial_Code` varchar(10) DEFAULT NULL,
  `Work_Contact_Number` varchar(255) DEFAULT NULL,
  `Fax_Dial_Code` varchar(10) DEFAULT NULL,
  `Fax_Number` varchar(255) DEFAULT NULL,
  `Mobile_Number` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `importbank`
--

DROP TABLE IF EXISTS `importbank`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `importbank` (
  `Bank_account_name` varchar(255) NOT NULL,
  `Account_number` varchar(255) NOT NULL,
  `Statement_reference` varchar(255) DEFAULT NULL,
  `DATE` date NOT NULL,
  `Balance` decimal(15,2) DEFAULT NULL,
  `Transaction_amount` decimal(15,2) NOT NULL,
  `Transaction_description` text,
  `INTERNAL_IDENTIFICATION` varchar(255) DEFAULT NULL,
  `Specialist` varchar(255) DEFAULT NULL,
  `Date_identified` date DEFAULT NULL,
  `Fiscal` varchar(255) DEFAULT NULL,
  `Comments` text,
  `Interim_fiscal` varchar(255) DEFAULT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `Reconned` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=49 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `internal_funds`
--

DROP TABLE IF EXISTS `internal_funds`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `internal_funds` (
  `A_Company_Code` varchar(225) DEFAULT NULL,
  `B_Company_Name` varchar(225) DEFAULT NULL,
  `Source` varchar(10) DEFAULT 'Internal',
  `D_Company_Status` varchar(225) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `internal_mg_list`
--

DROP TABLE IF EXISTS `internal_mg_list`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `internal_mg_list` (
  `A_Company_Code` varchar(255) DEFAULT NULL,
  `B_Company_Name` varchar(255) DEFAULT NULL,
  `C_Agent` varchar(255) DEFAULT NULL,
  `D_Company_Status` varchar(255) DEFAULT NULL,
  `E_Payment_Method` varchar(255) DEFAULT NULL,
  `F_Billing_Method` varchar(255) DEFAULT NULL,
  `G_Current_Fiscal` varchar(255) DEFAULT NULL,
  `H_Current_Status` varchar(255) DEFAULT NULL,
  `I_Last_Recon` varchar(255) DEFAULT NULL,
  `J_Arrears` varchar(255) DEFAULT NULL,
  `CONTACT_EMAIL` varchar(255) DEFAULT NULL,
  `recon_contact_1_name` varchar(255) DEFAULT NULL,
  `recon_contact_1_email` varchar(255) DEFAULT NULL,
  `recon_contact_2_name` varchar(255) DEFAULT NULL,
  `recon_contact_2_email` varchar(255) DEFAULT NULL,
  `Commencement_Date` date DEFAULT NULL,
  `Fund_status` varchar(255) DEFAULT NULL,
  `fund_status_date` date DEFAULT NULL,
  KEY `idx_mg_list_company_code` (`A_Company_Code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `internal_mg_notes`
--

DROP TABLE IF EXISTS `internal_mg_notes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `internal_mg_notes` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `Member_Group_Code` varchar(255) NOT NULL,
  `date` datetime NOT NULL,
  `User_Name` varchar(255) NOT NULL,
  `notes` text,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `medical_correspondence`
--

DROP TABLE IF EXISTS `medical_correspondence`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `medical_correspondence` (
  `Member_Group_Code` varchar(255) NOT NULL,
  `Title` varchar(255) DEFAULT NULL,
  `First_Name` varchar(255) DEFAULT NULL,
  `Surname` varchar(255) DEFAULT NULL,
  `ID_Number` varchar(255) DEFAULT NULL,
  `Email_Address` varchar(255) DEFAULT NULL,
  `Work_Dial_Code` varchar(10) DEFAULT NULL,
  `Work_Contact_Number` varchar(255) DEFAULT NULL,
  `Fax_Dial_Code` varchar(10) DEFAULT NULL,
  `Fax_Number` varchar(255) DEFAULT NULL,
  `Mobile_Number` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`Member_Group_Code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `reconned_bank`
--

DROP TABLE IF EXISTS `reconned_bank`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `reconned_bank` (
  `id` int NOT NULL AUTO_INCREMENT,
  `bank_line_id` int NOT NULL,
  `company_code` varchar(225) DEFAULT NULL,
  `transaction_amount` decimal(15,2) DEFAULT NULL,
  `transaction_date` date DEFAULT NULL,
  `fiscal_date` date DEFAULT NULL,
  `review_note` varchar(255) DEFAULT NULL,
  `recon_status` varchar(50) DEFAULT NULL,
  `amount_settled` decimal(15,2) DEFAULT NULL,
  `review_note_text` text,
  `fiscal_period_date` date DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_recon_import` (`bank_line_id`),
  CONSTRAINT `fk_recon_import` FOREIGN KEY (`bank_line_id`) REFERENCES `importbank` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=51 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `section_13a`
--

DROP TABLE IF EXISTS `section_13a`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `section_13a` (
  `Member_Group_Code` varchar(255) DEFAULT NULL,
  `Title` varchar(255) DEFAULT NULL,
  `First_Name` varchar(255) DEFAULT NULL,
  `Surname` varchar(255) DEFAULT NULL,
  `ID_Number` varchar(255) DEFAULT NULL,
  `Email_Address` varchar(255) DEFAULT NULL,
  `Indemnity` varchar(225) DEFAULT NULL,
  `Work_Dial_Code` varchar(10) DEFAULT NULL,
  `Work_Contact_Number` varchar(255) DEFAULT NULL,
  `Fax_Dial_Code` varchar(10) DEFAULT NULL,
  `Fax_Number` varchar(255) DEFAULT NULL,
  `Mobile_Number` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `socialaccount_socialaccount`
--

DROP TABLE IF EXISTS `socialaccount_socialaccount`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `socialaccount_socialaccount` (
  `id` int NOT NULL AUTO_INCREMENT,
  `provider` varchar(200) NOT NULL,
  `uid` varchar(191) NOT NULL,
  `last_login` datetime(6) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  `extra_data` json NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `socialaccount_socialaccount_provider_uid_fc810c6e_uniq` (`provider`,`uid`),
  KEY `socialaccount_socialaccount_user_id_8146e70c_fk_auth_user_id` (`user_id`),
  CONSTRAINT `socialaccount_socialaccount_user_id_8146e70c_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `socialaccount_socialapp`
--

DROP TABLE IF EXISTS `socialaccount_socialapp`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `socialaccount_socialapp` (
  `id` int NOT NULL AUTO_INCREMENT,
  `provider` varchar(30) NOT NULL,
  `name` varchar(40) NOT NULL,
  `client_id` varchar(191) NOT NULL,
  `secret` varchar(191) NOT NULL,
  `key` varchar(191) NOT NULL,
  `provider_id` varchar(200) NOT NULL,
  `settings` json NOT NULL DEFAULT (_utf8mb4'{}'),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `socialaccount_socialapp_sites`
--

DROP TABLE IF EXISTS `socialaccount_socialapp_sites`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `socialaccount_socialapp_sites` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `socialapp_id` int NOT NULL,
  `site_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `socialaccount_socialapp_sites_socialapp_id_site_id_71a9a768_uniq` (`socialapp_id`,`site_id`),
  KEY `socialaccount_socialapp_sites_site_id_2579dee5_fk_django_site_id` (`site_id`),
  CONSTRAINT `socialaccount_social_socialapp_id_97fb6e7d_fk_socialacc` FOREIGN KEY (`socialapp_id`) REFERENCES `socialaccount_socialapp` (`id`),
  CONSTRAINT `socialaccount_socialapp_sites_site_id_2579dee5_fk_django_site_id` FOREIGN KEY (`site_id`) REFERENCES `django_site` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `socialaccount_socialtoken`
--

DROP TABLE IF EXISTS `socialaccount_socialtoken`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `socialaccount_socialtoken` (
  `id` int NOT NULL AUTO_INCREMENT,
  `token` longtext NOT NULL,
  `token_secret` longtext NOT NULL,
  `expires_at` datetime(6) DEFAULT NULL,
  `account_id` int NOT NULL,
  `app_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `socialaccount_socialtoken_app_id_account_id_fca4e0ac_uniq` (`app_id`,`account_id`),
  KEY `socialaccount_social_account_id_951f210e_fk_socialacc` (`account_id`),
  CONSTRAINT `socialaccount_social_account_id_951f210e_fk_socialacc` FOREIGN KEY (`account_id`) REFERENCES `socialaccount_socialaccount` (`id`),
  CONSTRAINT `socialaccount_social_app_id_636a42d7_fk_socialacc` FOREIGN KEY (`app_id`) REFERENCES `socialaccount_socialapp` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `unity_bill`
--

DROP TABLE IF EXISTS `unity_bill`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `unity_bill` (
  `id` int NOT NULL AUTO_INCREMENT,
  `A_CCDatesMonth` date DEFAULT NULL,
  `B_Fund_Code` varchar(20) DEFAULT NULL,
  `C_Company_Code` varchar(20) DEFAULT NULL,
  `D_Company_Name` varchar(255) DEFAULT NULL,
  `E_Active_Members` int DEFAULT NULL,
  `F_Pre_Bill_Date` date DEFAULT NULL,
  `G_Schedule_Date` date DEFAULT NULL,
  `H_Schedule_Amount` decimal(10,2) DEFAULT NULL,
  `I_Submitted_Date` date DEFAULT NULL,
  `J_Final_Date` date DEFAULT NULL,
  `is_reconciled` tinyint(1) DEFAULT '0',
  `surplus_created` decimal(10,2) DEFAULT '0.00',
  `salary_amount` decimal(15,2) NOT NULL DEFAULT '0.00',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=39 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `unity_claims`
--

DROP TABLE IF EXISTS `unity_claims`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `unity_claims` (
  `id` int NOT NULL AUTO_INCREMENT,
  `company_code` varchar(50) NOT NULL,
  `agent` varchar(100) DEFAULT NULL,
  `id_number` varchar(20) NOT NULL,
  `member_name` varchar(100) NOT NULL,
  `member_surname` varchar(100) NOT NULL,
  `mip_number` varchar(50) DEFAULT NULL,
  `claim_type` varchar(50) NOT NULL DEFAULT 'Withdrawal',
  `exit_reason` varchar(50) DEFAULT NULL,
  `claim_allocation` varchar(50) NOT NULL DEFAULT 'New Claim',
  `claim_status` varchar(50) NOT NULL DEFAULT 'Claim Docs Requested',
  `payment_option` varchar(50) DEFAULT NULL,
  `claim_created_date` date NOT NULL,
  `last_contribution_date` date DEFAULT NULL,
  `date_submitted` date DEFAULT NULL,
  `date_paid` date DEFAULT NULL,
  `linked_email_id` int DEFAULT NULL,
  `claim_amount` decimal(15,2) DEFAULT NULL,
  `vested_pot_available` tinyint(1) DEFAULT '0',
  `vested_pot_paid_date` date DEFAULT NULL,
  `savings_pot_available` tinyint(1) DEFAULT '0',
  `savings_pot_paid_date` date DEFAULT NULL,
  `infund_preservation_cert_received_date` date DEFAULT NULL,
  `qualified` varchar(10) DEFAULT 'YES',
  `date_submitted_online` date DEFAULT NULL,
  `informed_er` varchar(10) DEFAULT 'NO',
  `submitted_by_agent` varchar(50) DEFAULT NULL,
  `date_app_extracted` date DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_unity_claims_company_code` (`company_code`)
) ENGINE=InnoDB AUTO_INCREMENT=38 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `unity_internal_app_unityclaimnote`
--

DROP TABLE IF EXISTS `unity_internal_app_unityclaimnote`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `unity_internal_app_unityclaimnote` (
  `id` int NOT NULL AUTO_INCREMENT,
  `claim_id` int NOT NULL,
  `note_selection` varchar(255) DEFAULT NULL,
  `note_description` text,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `created_by_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `claim_id` (`claim_id`),
  CONSTRAINT `unity_internal_app_unityclaimnote_ibfk_1` FOREIGN KEY (`claim_id`) REFERENCES `unity_claims` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=42 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `unity_internal_delegationnote`
--

DROP TABLE IF EXISTS `unity_internal_delegationnote`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `unity_internal_delegationnote` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `delegation_id` bigint NOT NULL,
  `user_id` int DEFAULT NULL,
  `content` text NOT NULL,
  `created_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `delegation_id` (`delegation_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `unity_internal_delegationnote_ibfk_1` FOREIGN KEY (`delegation_id`) REFERENCES `unity_internal_emaildelegation` (`id`),
  CONSTRAINT `unity_internal_delegationnote_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=27 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `unity_internal_delegationtransactionlog`
--

DROP TABLE IF EXISTS `unity_internal_delegationtransactionlog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `unity_internal_delegationtransactionlog` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `delegation_id` bigint NOT NULL,
  `user_id` int DEFAULT NULL,
  `action_type` varchar(50) NOT NULL,
  `subject` varchar(255) NOT NULL,
  `recipient_email` varchar(254) NOT NULL,
  `timestamp` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `delegation_id` (`delegation_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `unity_internal_delegationtransactionlog_ibfk_1` FOREIGN KEY (`delegation_id`) REFERENCES `unity_internal_emaildelegation` (`id`),
  CONSTRAINT `unity_internal_delegationtransactionlog_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=38 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `unity_internal_emaildelegation`
--

DROP TABLE IF EXISTS `unity_internal_emaildelegation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `unity_internal_emaildelegation` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `email_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `assigned_user_id` int DEFAULT NULL,
  `status` varchar(3) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `delegated_at` datetime(6) DEFAULT NULL,
  `received_at` datetime(6) DEFAULT NULL,
  `company_code` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `email_category` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `work_related` tinyint(1) NOT NULL DEFAULT '1',
  `communication_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email_id` (`email_id`),
  KEY `assigned_user_id` (`assigned_user_id`),
  CONSTRAINT `unity_internal_emaildelegation_ibfk_1` FOREIGN KEY (`assigned_user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=115 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `unity_internal_inbox`
--

DROP TABLE IF EXISTS `unity_internal_inbox`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `unity_internal_inbox` (
  `email_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `subject` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `sender_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `sender_address` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `body_content` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `received_at` datetime DEFAULT NULL,
  PRIMARY KEY (`email_id`),
  KEY `idx_received_at` (`received_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `unity_internal_outlooktoken`
--

DROP TABLE IF EXISTS `unity_internal_outlooktoken`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `unity_internal_outlooktoken` (
  `user_principal_name` varchar(255) NOT NULL,
  `access_token` text NOT NULL,
  `refresh_token` text,
  `expires_in_seconds` int NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`user_principal_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `unity_journal_entry`
--

DROP TABLE IF EXISTS `unity_journal_entry`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `unity_journal_entry` (
  `id` int NOT NULL AUTO_INCREMENT,
  `surplus_source_id` int NOT NULL,
  `target_bill_id` int NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `allocation_date` date NOT NULL,
  `created_by` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_surplus_source` (`surplus_source_id`),
  KEY `idx_target_bill` (`target_bill_id`),
  CONSTRAINT `fk_journal_bill` FOREIGN KEY (`target_bill_id`) REFERENCES `unity_bill` (`id`),
  CONSTRAINT `fk_journal_surplus` FOREIGN KEY (`surplus_source_id`) REFERENCES `unity_schedule_surplus` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `unity_notes`
--

DROP TABLE IF EXISTS `unity_notes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `unity_notes` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `Member Group Code` text,
  `date` datetime DEFAULT NULL,
  `User` text,
  `notes` text,
  `Communication_Type` varchar(90) DEFAULT NULL,
  `Action_Notes` varchar(90) DEFAULT NULL,
  `attached_email_id` varchar(255) DEFAULT NULL,
  `attached_file_name` varchar(255) DEFAULT NULL,
  `attached_file` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB AUTO_INCREMENT=63 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `unity_schedule_surplus`
--

DROP TABLE IF EXISTS `unity_schedule_surplus`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `unity_schedule_surplus` (
  `id` int NOT NULL AUTO_INCREMENT,
  `unity_bill_source_id` int NOT NULL,
  `surplus_amount` decimal(10,2) NOT NULL,
  `creation_date` date NOT NULL,
  `generating_credit_note_id` int DEFAULT NULL,
  `status` varchar(20) NOT NULL DEFAULT 'UNAPPLIED',
  PRIMARY KEY (`id`),
  KEY `unity_bill_source_id` (`unity_bill_source_id`),
  KEY `generating_credit_note_id` (`generating_credit_note_id`),
  CONSTRAINT `unity_schedule_surplus_ibfk_1` FOREIGN KEY (`unity_bill_source_id`) REFERENCES `unity_bill` (`id`),
  CONSTRAINT `unity_schedule_surplus_ibfk_2` FOREIGN KEY (`generating_credit_note_id`) REFERENCES `credit_note` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-06-29 22:13:10
