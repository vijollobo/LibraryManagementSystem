-- MySQL dump 10.13  Distrib 8.0.40, for Win64 (x86_64)
--
-- Host: localhost    Database: library
-- ------------------------------------------------------
-- Server version	8.0.40

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
-- Table structure for table `books`
--

DROP TABLE IF EXISTS `books`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `books` (
  `ISBN` char(13) NOT NULL,
  `name` varchar(200) NOT NULL,
  `author` varchar(150) NOT NULL,
  `language` varchar(50) NOT NULL,
  `genre` varchar(50) NOT NULL,
  `publisher` varchar(100) NOT NULL,
  `cost` float NOT NULL,
  `quantity` int NOT NULL,
  `native_name` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`ISBN`),
  CONSTRAINT `books_chk_1` CHECK ((`cost` > 0.0)),
  CONSTRAINT `books_chk_2` CHECK ((`quantity` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `books`
--

LOCK TABLES `books` WRITE;
/*!40000 ALTER TABLE `books` DISABLE KEYS */;
INSERT INTO `books` VALUES ('9780143031031','The Discovery of India','Jawaharlal Nehru','English','History','Oxford University Press',600,59,NULL),('9787804155187','Vhadle Ghar','Uday Bhembre','Konkani','History','Sanjana Publications',300,10,'व्हडलें घर'),('9788126702343','Pratinidhi Vyangya','Harishankar Parsai','Hindi','Satire','Bhasha Publications',98,10,'प्रतिनिधि व्यंग्य'),('9788172290085','The Story of My Experiments with Truth','Mahatma Gandhi','English','Auto-biography','Navjivan Publishing Trust',100,16,NULL),('9788173392153','Burhi Aair Xadhu','Lakshminath Bezbaruah','Axomiya','Short Stories','Panchajanya Publishing',130,10,'বুঢ়ী আইৰ সাধু'),('9788175226036','Ghore Baire','Rabindranath Thakur','Bangla','Novel','Viswa Bharati Publishers',245,9,'ঘরে বাইরে'),('9788183742313','Shesher Kobita','Rabindranath Thakur','Bangla','Novel','Viswa Bharati Publishers',100,12,'শেষের কবিতা'),('9788189059637','Annihilation of Caste','Dr. B. R. Ambedkar','English','Non-fiction','Yugsakshi Publication',80,10,NULL),('9788195805877','Anandamath','Bankim Chandra Chattopadhyay','Bangla','Novel','Bhasha Publications',100,60,'আনন্দমঠ'),('9788196396152','Kokadeuta Aru Natilora','Lakshminath Bezbaruah','Axomiya','Short Stories','Panchajanya Publishing',200,11,'ককা দেউতা আৰু নাতিল\'ৰা'),('9789372770353','1984','George Orwell','English','Novel','Himanshu Publications',249,22,NULL),('9789383064656','An Era of Darkness','Shashi Tharoor','English','History','Aleph Book Company',699,34,NULL),('9789392147944','Why I Am An Atheist And Other Works','Bhagat Singh','English','Auto-biography','Om SaiTech Books Publishers & Distributors',199,74,NULL),('9878175221758','Golpoguchchho','Rabindranath Thakur','Bangla','Short Stories','Viswa Bharati Publishers',800,1,'গল্পগুচ্ছ'),('9878177868326','Vangachitre','Purushottam Laxman Deshpande','Marathi','Novel','Saket Prakashan',300,15,'वंगचित्रे');
/*!40000 ALTER TABLE `books` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `issued_books`
--

DROP TABLE IF EXISTS `issued_books`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `issued_books` (
  `IssueCode` char(5) NOT NULL,
  `ISBN` char(13) DEFAULT NULL,
  `username` varchar(20) DEFAULT NULL,
  `issueDate` date DEFAULT NULL,
  `dueDate` date DEFAULT NULL,
  `returnDate` date DEFAULT NULL,
  `status` enum('ISSUED','RETURNED') DEFAULT 'ISSUED',
  `accruedCost` decimal(10,2) DEFAULT NULL,
  `accruedFine` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`IssueCode`),
  KEY `ISBN` (`ISBN`),
  KEY `username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `issued_books`
--

LOCK TABLES `issued_books` WRITE;
/*!40000 ALTER TABLE `issued_books` DISABLE KEYS */;
INSERT INTO `issued_books` VALUES ('9OHS4','9787804155187','Mervis','2026-02-08','2026-03-08',NULL,'ISSUED',NULL,NULL),('RZH1N','9780143031031','vijol','2026-02-09','2026-03-09',NULL,'ISSUED',NULL,NULL),('WN2JK','9789383064656','soyam','2026-02-09','2026-03-18',NULL,'ISSUED',NULL,NULL);
/*!40000 ALTER TABLE `issued_books` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `requested_books`
--

DROP TABLE IF EXISTS `requested_books`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `requested_books` (
  `requestID` char(5) NOT NULL,
  `username` varchar(20) DEFAULT NULL,
  `ISBN` char(13) DEFAULT NULL,
  `requestDate` date DEFAULT NULL,
  PRIMARY KEY (`requestID`),
  KEY `username` (`username`),
  KEY `ISBN` (`ISBN`),
  CONSTRAINT `requested_books_ibfk_2` FOREIGN KEY (`ISBN`) REFERENCES `books` (`ISBN`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `requested_books`
--

LOCK TABLES `requested_books` WRITE;
/*!40000 ALTER TABLE `requested_books` DISABLE KEYS */;
INSERT INTO `requested_books` VALUES ('2438L','testuser','9878175221758','2026-02-08'),('6I5OI','testuser','9788172290085','2026-02-08'),('GST65','testuser','9788172290085','2026-02-08'),('VRM9W','testuser','9878175221758','2026-02-08'),('XTPWE','soyam','9789372770353','2026-02-09');
/*!40000 ALTER TABLE `requested_books` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `username` varchar(20) NOT NULL,
  `name` varchar(200) NOT NULL,
  `email` varchar(75) NOT NULL,
  `phone` char(10) NOT NULL,
  `gender` varchar(30) DEFAULT NULL,
  `dob` date NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `role` enum('admin','user') DEFAULT 'user',
  `security_q` int NOT NULL,
  `security_ans` varchar(255) NOT NULL,
  PRIMARY KEY (`username`),
  UNIQUE KEY `email` (`email`),
  UNIQUE KEY `phone` (`phone`),
  CONSTRAINT `chk_phone` CHECK (regexp_like(`phone`,_utf8mb4'^[6-9][0-9]{9}$')),
  CONSTRAINT `chk_security_q` CHECK ((`security_q` between 1 and 5))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES ('admin','Library Admin','admin@library.com','9870571257',NULL,'2000-01-01','7676aaafb027c825bd9abab78b234070e702752f625b752e55e55b48e607e358','admin',5,'8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918'),('Mervis','Mervis Mascerhanas','mervism@goamail.com','9870571252','Cisgender Male','2003-01-15','d18710d6440962c17545bf546aa1f59dcb9939f9fd774e403784be2c8cf17054','user',3,'Fish Fry'),('soyam','Soyam Rai','soyamrai18@gmail.com','9883865433','Cisgender Male','2005-05-18','5810ad6e8bdd9dceda67380257239fcfdc6193c4e39ce66c50af3600f5d4a2fc','user',5,'kk'),('vijol','Vijol Lobo','vijoljlobo@gmail.com','9870571255','Cisgender Male','2005-12-07','157dd3b19eb9f1f5ebec706ff0dd807dd91d8e6eca871fc15a03b8a8401d3fd8','user',2,'Ambar');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-03-03  3:54:01
