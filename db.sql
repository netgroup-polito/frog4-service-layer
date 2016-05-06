# noinspection SqlNoDataSourceInspectionForFile
-- phpMyAdmin SQL Dump
-- version 4.4.10
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: Nov 13, 2015 at 03:39 PM
-- Server version: 5.5.42
-- PHP Version: 5.6.10

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";

--
-- Database: `service_layer`
--

-- --------------------------------------------------------

--
-- Table structure for table `node`
--

CREATE TABLE IF NOT EXISTS `node` (
  `id` varchar(64) NOT NULL,
  `name` varchar(64) NOT NULL,
  `domain_id` varchar(64) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `session`
--

CREATE TABLE IF NOT EXISTS `session` (
  `id` varchar(64) NOT NULL,
  `user_id` varchar(64) DEFAULT NULL,
  `service_graph_id` varchar(64) NOT NULL,
  `service_graph_name` varchar(64) NOT NULL,
  `ingress_node` varchar(64) DEFAULT NULL,
  `egress_node` varchar(64) DEFAULT NULL,
  `status` varchar(64) NOT NULL,
  `started_at` datetime DEFAULT NULL,
  `last_update` datetime DEFAULT NULL,
  `error` datetime DEFAULT NULL,
  `ended` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `user`
--

CREATE TABLE IF NOT EXISTS `user` (
  `id` varchar(64) CHARACTER SET utf8 NOT NULL,
  `name` varchar(64) CHARACTER SET utf8 NOT NULL,
  `password` varchar(64) CHARACTER SET utf8 NOT NULL,
  `tenant_id` varchar(64) CHARACTER SET utf8 NOT NULL,
  `mail` varchar(64) CHARACTER SET utf8 DEFAULT NULL,
  `service_graph` text NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `tenant`
--

CREATE TABLE IF NOT EXISTS `tenant` (
  `id` varchar(64) CHARACTER SET utf8 NOT NULL,
  `name` varchar(64) CHARACTER SET utf8 NOT NULL,
  `description` varchar(128) CHARACTER SET utf8 NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `vnf_image`
--

CREATE TABLE IF NOT EXISTS `vnf_image` (
  `id` varchar(255) NOT NULL,
  `internal_id` varchar(255) NOT NULL,
  `template` text NOT NULL,
  `configuration_model` text,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `user_device`
--

CREATE TABLE IF NOT EXISTS `user_device` (
  `session_id` varchar(64) NOT NULL,
  `mac_address` varchar(64) NOT NULL,
  `endpoint_id` varchar(64) NOT NULL,
  `endpoint_db_id` varchar(64) NOT NULL,
  PRIMARY KEY (`session_id`, `mac_address`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `user_location`
--

CREATE TABLE IF NOT EXISTS `user_location` (
  `user_id` varchar(64) NOT NULL,
  `node_id` varchar(64) NOT NULL,
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `domain`
--

CREATE TABLE IF NOT EXISTS `domain` (
  `id` int(11) NOT NULL,
  `name` varchar(64) COLLATE utf8_unicode_ci NOT NULL,
  `type` varchar(64) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `domain_information`
--

CREATE TABLE IF NOT EXISTS `domain_information` (
  `id` int(64) NOT NULL,
  `domain_id` int(11) NOT NULL,
  `node` varchar(64) COLLATE utf8_unicode_ci DEFAULT NULL,
  `interface` varchar(64) COLLATE utf8_unicode_ci NOT NULL,
  `interface_type` varchar(64) COLLATE utf8_unicode_ci DEFAULT NULL,
  `gre` tinyint(1) NOT NULL,
  `vlan` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `domain_gre`
--

CREATE TABLE IF NOT EXISTS `domain_gre` (
  `id` int(64) NOT NULL,
  `name` varchar(64) COLLATE utf8_unicode_ci NOT NULL,
  `domain_info_id` int(64) NOT NULL,
  `local_ip` varchar(64) COLLATE utf8_unicode_ci NOT NULL,
  `remote_ip` varchar(64) COLLATE utf8_unicode_ci DEFAULT NULL,
  `gre_key` varchar(64) COLLATE utf8_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `domain_neighbor`
--

CREATE TABLE IF NOT EXISTS `domain_neighbor` (
  `id` int(11) NOT NULL,
  `domain_info_id` int(11) NOT NULL,
  `neighbor_domain_name` varchar(64) COLLATE utf8_unicode_ci NOT NULL,
  `neighbor_node` varchar(64) COLLATE utf8_unicode_ci DEFAULT NULL,
  `neighbor_interface` varchar(64) COLLATE utf8_unicode_ci DEFAULT NULL,
  `neighbor_domain_type` varchar(64) COLLATE utf8_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `end_point`
--

CREATE TABLE IF NOT EXISTS `end_point` (
  `id` int(64) NOT NULL,
  `name` varchar(64) COLLATE utf8_unicode_ci NOT NULL,
  `type` varchar(64) COLLATE utf8_unicode_ci NOT NULL,
  `domain_name` varchar(64) COLLATE utf8_unicode_ci DEFAULT NULL,
  `interface` varchar(64) COLLATE utf8_unicode_ci,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;


-- --------------------------------------------------------

--
-- Table structure for table `graph`
--

CREATE TABLE IF NOT EXISTS `graph` (
  `id` int(64) NOT NULL,
  `session_id` varchar(64) NOT NULL,
  `domain_id` int(11) DEFAULT NULL,
  `partial` tinyint(4) DEFAULT NULL,
  `service_graph` text NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `service_graph_id` (`session_id`,`domain_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Dumping data for table `user`
--

REPLACE INTO `user` (`id`, `name`, `password`, `tenant_id`, `service_graph`) VALUES
('0', 'admin', 'qwerty', '0', 'authentication_graph.json'),
('1', 'user1', 'password1', '2', 'client_graph_1.json'),
('2', 'isp', 'isp', '1', 'isp_graph.json'),
('3', 'user2', 'password1', '2', 'client_graph_2.json');
--
-- Dumping data for table `node`
--

-- REPLACE INTO `node` (`id`, `name`, `domain_id`) VALUES
-- ('0', 'node0', '130.192.225.105'),
-- ('1', 'node1', '130.192.225.193'),
-- ('2', 'node2', '10.0.0.3'),
-- ('3', 'node3', '10.0.0.4'),
-- ('4', 'node4', '10.0.0.5');

--
-- Dumping data for table `user_location`
--

-- REPLACE INTO `user_location` (`user_id`, `node_id`) VALUES
-- ('0', '0');

--
-- Dumping data for table `tenant`
--

REPLACE INTO `tenant` (`id`, `name`, `description`) VALUES
('0', 'admin', 'admin tenant'),
('1', 'isp', 'isp tenant'),
('2', 'public', 'public tenant');


