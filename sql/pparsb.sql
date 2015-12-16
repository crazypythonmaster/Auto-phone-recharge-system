-- phpMyAdmin SQL Dump
-- version 4.0.10deb1
-- http://www.phpmyadmin.net
--
-- Хост: localhost
-- Время создания: Фев 03 2015 г., 17:22
-- Версия сервера: 5.5.41-0ubuntu0.14.04.1
-- Версия PHP: 5.5.9-1ubuntu4.5

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- База данных: `pparsb`
--

-- --------------------------------------------------------

--
-- Структура таблицы `auth_group`
--

CREATE TABLE IF NOT EXISTS `auth_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Структура таблицы `auth_group_permissions`
--

CREATE TABLE IF NOT EXISTS `auth_group_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `group_id` (`group_id`,`permission_id`),
  KEY `auth_group_permissions_5f412f9a` (`group_id`),
  KEY `auth_group_permissions_83d7f98b` (`permission_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Структура таблицы `auth_permission`
--

CREATE TABLE IF NOT EXISTS `auth_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `content_type_id` (`content_type_id`,`codename`),
  KEY `auth_permission_37ef4eb4` (`content_type_id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8 AUTO_INCREMENT=100 ;

--
-- Дамп данных таблицы `auth_permission`
--

INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES
(1, 'Can add log entry', 1, 'add_logentry'),
(2, 'Can change log entry', 1, 'change_logentry'),
(3, 'Can delete log entry', 1, 'delete_logentry'),
(4, 'Can add permission', 2, 'add_permission'),
(5, 'Can change permission', 2, 'change_permission'),
(6, 'Can delete permission', 2, 'delete_permission'),
(7, 'Can add group', 3, 'add_group'),
(8, 'Can change group', 3, 'change_group'),
(9, 'Can delete group', 3, 'delete_group'),
(10, 'Can add user', 4, 'add_user'),
(11, 'Can change user', 4, 'change_user'),
(12, 'Can delete user', 4, 'delete_user'),
(13, 'Can add content type', 5, 'add_contenttype'),
(14, 'Can change content type', 5, 'change_contenttype'),
(15, 'Can delete content type', 5, 'delete_contenttype'),
(16, 'Can add session', 6, 'add_session'),
(17, 'Can change session', 6, 'change_session'),
(18, 'Can delete session', 6, 'delete_session'),
(19, 'Can add migration history', 7, 'add_migrationhistory'),
(20, 'Can change migration history', 7, 'change_migrationhistory'),
(21, 'Can delete migration history', 7, 'delete_migrationhistory'),
(22, 'Can add task state', 8, 'add_taskmeta'),
(23, 'Can change task state', 8, 'change_taskmeta'),
(24, 'Can delete task state', 8, 'delete_taskmeta'),
(25, 'Can add saved group result', 9, 'add_tasksetmeta'),
(26, 'Can change saved group result', 9, 'change_tasksetmeta'),
(27, 'Can delete saved group result', 9, 'delete_tasksetmeta'),
(28, 'Can add interval', 10, 'add_intervalschedule'),
(29, 'Can change interval', 10, 'change_intervalschedule'),
(30, 'Can delete interval', 10, 'delete_intervalschedule'),
(31, 'Can add crontab', 11, 'add_crontabschedule'),
(32, 'Can change crontab', 11, 'change_crontabschedule'),
(33, 'Can delete crontab', 11, 'delete_crontabschedule'),
(34, 'Can add periodic tasks', 12, 'add_periodictasks'),
(35, 'Can change periodic tasks', 12, 'change_periodictasks'),
(36, 'Can delete periodic tasks', 12, 'delete_periodictasks'),
(37, 'Can add periodic task', 13, 'add_periodictask'),
(38, 'Can change periodic task', 13, 'change_periodictask'),
(39, 'Can delete periodic task', 13, 'delete_periodictask'),
(40, 'Can add worker', 14, 'add_workerstate'),
(41, 'Can change worker', 14, 'change_workerstate'),
(42, 'Can delete worker', 14, 'delete_workerstate'),
(43, 'Can add task', 15, 'add_taskstate'),
(44, 'Can change task', 15, 'change_taskstate'),
(45, 'Can delete task', 15, 'delete_taskstate'),
(46, 'Can add company profile', 16, 'add_companyprofile'),
(47, 'Can change company profile', 16, 'change_companyprofile'),
(48, 'Can delete company profile', 16, 'delete_companyprofile'),
(49, 'Can add user profile', 17, 'add_userprofile'),
(50, 'Can change user profile', 17, 'change_userprofile'),
(51, 'Can delete user profile', 17, 'delete_userprofile'),
(52, 'Can add customer', 18, 'add_customer'),
(53, 'Can change customer', 18, 'change_customer'),
(54, 'Can delete customer', 18, 'delete_customer'),
(55, 'Can add phone number', 19, 'add_phonenumber'),
(56, 'Can change phone number', 19, 'change_phonenumber'),
(57, 'Can delete phone number', 19, 'delete_phonenumber'),
(58, 'Can add carrier', 20, 'add_carrier'),
(59, 'Can change carrier', 20, 'change_carrier'),
(60, 'Can delete carrier', 20, 'delete_carrier'),
(61, 'Can add carrier admin', 21, 'add_carrieradmin'),
(62, 'Can change carrier admin', 21, 'change_carrieradmin'),
(63, 'Can delete carrier admin', 21, 'delete_carrieradmin'),
(64, 'Can add plan', 22, 'add_plan'),
(65, 'Can change plan', 22, 'change_plan'),
(66, 'Can delete plan', 22, 'delete_plan'),
(67, 'Can add plan discount', 23, 'add_plandiscount'),
(68, 'Can change plan discount', 23, 'change_plandiscount'),
(69, 'Can delete plan discount', 23, 'delete_plandiscount'),
(70, 'Can add auto refill', 24, 'add_autorefill'),
(71, 'Can change auto refill', 24, 'change_autorefill'),
(72, 'Can delete auto refill', 24, 'delete_autorefill'),
(73, 'Can add transaction', 25, 'add_transaction'),
(74, 'Can change transaction', 25, 'change_transaction'),
(75, 'Can delete transaction', 25, 'delete_transaction'),
(76, 'Can add transaction step', 26, 'add_transactionstep'),
(77, 'Can change transaction step', 26, 'change_transactionstep'),
(78, 'Can delete transaction step', 26, 'delete_transactionstep'),
(79, 'Can add credit card charge', 27, 'add_creditcardcharge'),
(80, 'Can change credit card charge', 27, 'change_creditcardcharge'),
(81, 'Can delete credit card charge', 27, 'delete_creditcardcharge'),
(82, 'Can add unused pin', 28, 'add_unusedpin'),
(83, 'Can change unused pin', 28, 'change_unusedpin'),
(84, 'Can delete unused pin', 28, 'delete_unusedpin'),
(85, 'Can add log', 29, 'add_log'),
(86, 'Can change log', 29, 'change_log'),
(87, 'Can delete log', 29, 'delete_log'),
(88, 'Can add spam message', 30, 'add_spammessage'),
(89, 'Can change spam message', 30, 'change_spammessage'),
(90, 'Can delete spam message', 30, 'delete_spammessage'),
(91, 'Can add captcha logs', 31, 'add_captchalogs'),
(92, 'Can change captcha logs', 31, 'change_captchalogs'),
(93, 'Can delete captcha logs', 31, 'delete_captchalogs'),
(94, 'Can add command log', 32, 'add_commandlog'),
(95, 'Can change command log', 32, 'change_commandlog'),
(96, 'Can delete command log', 32, 'delete_commandlog'),
(97, 'Can add confirm dp', 33, 'add_confirmdp'),
(98, 'Can change confirm dp', 33, 'change_confirmdp'),
(99, 'Can delete confirm dp', 33, 'delete_confirmdp');

-- --------------------------------------------------------

--
-- Структура таблицы `auth_user`
--

CREATE TABLE IF NOT EXISTS `auth_user` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime NOT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(30) NOT NULL,
  `first_name` varchar(30) NOT NULL,
  `last_name` varchar(30) NOT NULL,
  `email` varchar(75) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Структура таблицы `auth_user_groups`
--

CREATE TABLE IF NOT EXISTS `auth_user_groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`,`group_id`),
  KEY `auth_user_groups_6340c63c` (`user_id`),
  KEY `auth_user_groups_5f412f9a` (`group_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Структура таблицы `auth_user_user_permissions`
--

CREATE TABLE IF NOT EXISTS `auth_user_user_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`,`permission_id`),
  KEY `auth_user_user_permissions_6340c63c` (`user_id`),
  KEY `auth_user_user_permissions_83d7f98b` (`permission_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Структура таблицы `celery_taskmeta`
--

CREATE TABLE IF NOT EXISTS `celery_taskmeta` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `task_id` varchar(255) NOT NULL,
  `status` varchar(50) NOT NULL,
  `result` longtext,
  `date_done` datetime NOT NULL,
  `traceback` longtext,
  `hidden` tinyint(1) NOT NULL,
  `meta` longtext,
  PRIMARY KEY (`id`),
  UNIQUE KEY `task_id` (`task_id`),
  KEY `celery_taskmeta_2ff6b945` (`hidden`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Структура таблицы `celery_tasksetmeta`
--

CREATE TABLE IF NOT EXISTS `celery_tasksetmeta` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `taskset_id` varchar(255) NOT NULL,
  `result` longtext NOT NULL,
  `date_done` datetime NOT NULL,
  `hidden` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `taskset_id` (`taskset_id`),
  KEY `celery_tasksetmeta_2ff6b945` (`hidden`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Структура таблицы `django_admin_log`
--

CREATE TABLE IF NOT EXISTS `django_admin_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `action_time` datetime NOT NULL,
  `user_id` bigint(20) NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_6340c63c` (`user_id`),
  KEY `django_admin_log_37ef4eb4` (`content_type_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Структура таблицы `django_content_type`
--

CREATE TABLE IF NOT EXISTS `django_content_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `app_label` (`app_label`,`model`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8 AUTO_INCREMENT=34 ;

--
-- Дамп данных таблицы `django_content_type`
--

INSERT INTO `django_content_type` (`id`, `name`, `app_label`, `model`) VALUES
(1, 'log entry', 'admin', 'logentry'),
(2, 'permission', 'auth', 'permission'),
(3, 'group', 'auth', 'group'),
(4, 'user', 'auth', 'user'),
(5, 'content type', 'contenttypes', 'contenttype'),
(6, 'session', 'sessions', 'session'),
(7, 'migration history', 'south', 'migrationhistory'),
(8, 'task state', 'djcelery', 'taskmeta'),
(9, 'saved group result', 'djcelery', 'tasksetmeta'),
(10, 'interval', 'djcelery', 'intervalschedule'),
(11, 'crontab', 'djcelery', 'crontabschedule'),
(12, 'periodic tasks', 'djcelery', 'periodictasks'),
(13, 'periodic task', 'djcelery', 'periodictask'),
(14, 'worker', 'djcelery', 'workerstate'),
(15, 'task', 'djcelery', 'taskstate'),
(16, 'company profile', 'core', 'companyprofile'),
(17, 'user profile', 'core', 'userprofile'),
(18, 'customer', 'core', 'customer'),
(19, 'phone number', 'core', 'phonenumber'),
(20, 'carrier', 'core', 'carrier'),
(21, 'carrier admin', 'core', 'carrieradmin'),
(22, 'plan', 'core', 'plan'),
(23, 'plan discount', 'core', 'plandiscount'),
(24, 'auto refill', 'core', 'autorefill'),
(25, 'transaction', 'core', 'transaction'),
(26, 'transaction step', 'core', 'transactionstep'),
(27, 'credit card charge', 'core', 'creditcardcharge'),
(28, 'unused pin', 'core', 'unusedpin'),
(29, 'log', 'core', 'log'),
(30, 'spam message', 'core', 'spammessage'),
(31, 'captcha logs', 'core', 'captchalogs'),
(32, 'command log', 'core', 'commandlog'),
(33, 'confirm dp', 'core', 'confirmdp');

-- --------------------------------------------------------

--
-- Структура таблицы `django_session`
--

CREATE TABLE IF NOT EXISTS `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_b7b81f0c` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Структура таблицы `djcelery_crontabschedule`
--

CREATE TABLE IF NOT EXISTS `djcelery_crontabschedule` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `minute` varchar(64) NOT NULL,
  `hour` varchar(64) NOT NULL,
  `day_of_week` varchar(64) NOT NULL,
  `day_of_month` varchar(64) NOT NULL,
  `month_of_year` varchar(64) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Структура таблицы `djcelery_intervalschedule`
--

CREATE TABLE IF NOT EXISTS `djcelery_intervalschedule` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `every` int(11) NOT NULL,
  `period` varchar(24) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Структура таблицы `djcelery_periodictask`
--

CREATE TABLE IF NOT EXISTS `djcelery_periodictask` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `task` varchar(200) NOT NULL,
  `interval_id` int(11) DEFAULT NULL,
  `crontab_id` int(11) DEFAULT NULL,
  `args` longtext NOT NULL,
  `kwargs` longtext NOT NULL,
  `queue` varchar(200) DEFAULT NULL,
  `exchange` varchar(200) DEFAULT NULL,
  `routing_key` varchar(200) DEFAULT NULL,
  `expires` datetime DEFAULT NULL,
  `enabled` tinyint(1) NOT NULL,
  `last_run_at` datetime DEFAULT NULL,
  `total_run_count` int(10) unsigned NOT NULL,
  `date_changed` datetime NOT NULL,
  `description` longtext NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `djcelery_periodictask_8905f60d` (`interval_id`),
  KEY `djcelery_periodictask_7280124f` (`crontab_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Структура таблицы `djcelery_periodictasks`
--

CREATE TABLE IF NOT EXISTS `djcelery_periodictasks` (
  `ident` smallint(6) NOT NULL,
  `last_update` datetime NOT NULL,
  PRIMARY KEY (`ident`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Структура таблицы `djcelery_taskstate`
--

CREATE TABLE IF NOT EXISTS `djcelery_taskstate` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `state` varchar(64) NOT NULL,
  `task_id` varchar(36) NOT NULL,
  `name` varchar(200) DEFAULT NULL,
  `tstamp` datetime NOT NULL,
  `args` longtext,
  `kwargs` longtext,
  `eta` datetime DEFAULT NULL,
  `expires` datetime DEFAULT NULL,
  `result` longtext,
  `traceback` longtext,
  `runtime` double DEFAULT NULL,
  `retries` int(11) NOT NULL,
  `worker_id` int(11) DEFAULT NULL,
  `hidden` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `task_id` (`task_id`),
  KEY `djcelery_taskstate_5654bf12` (`state`),
  KEY `djcelery_taskstate_4da47e07` (`name`),
  KEY `djcelery_taskstate_abaacd02` (`tstamp`),
  KEY `djcelery_taskstate_cac6a03d` (`worker_id`),
  KEY `djcelery_taskstate_2ff6b945` (`hidden`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Структура таблицы `djcelery_workerstate`
--

CREATE TABLE IF NOT EXISTS `djcelery_workerstate` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `hostname` varchar(255) NOT NULL,
  `last_heartbeat` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `hostname` (`hostname`),
  KEY `djcelery_workerstate_11e400ef` (`last_heartbeat`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Структура таблицы `south_migrationhistory`
--

CREATE TABLE IF NOT EXISTS `south_migrationhistory` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app_name` varchar(255) NOT NULL,
  `migration` varchar(255) NOT NULL,
  `applied` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8 AUTO_INCREMENT=5 ;

--
-- Дамп данных таблицы `south_migrationhistory`
--

INSERT INTO `south_migrationhistory` (`id`, `app_name`, `migration`, `applied`) VALUES
(1, 'djcelery', '0001_initial', '2015-02-03 15:14:14'),
(2, 'djcelery', '0002_v25_changes', '2015-02-03 15:14:15'),
(3, 'djcelery', '0003_v26_changes', '2015-02-03 15:14:15'),
(4, 'djcelery', '0004_v30_changes', '2015-02-03 15:14:15');

--
-- Ограничения внешнего ключа сохраненных таблиц
--

--
-- Ограничения внешнего ключа таблицы `auth_group_permissions`
--
ALTER TABLE `auth_group_permissions`
  ADD CONSTRAINT `group_id_refs_id_f4b32aac` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  ADD CONSTRAINT `permission_id_refs_id_6ba0f519` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`);

--
-- Ограничения внешнего ключа таблицы `auth_permission`
--
ALTER TABLE `auth_permission`
  ADD CONSTRAINT `content_type_id_refs_id_d043b34a` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`);

--
-- Ограничения внешнего ключа таблицы `auth_user_groups`
--
ALTER TABLE `auth_user_groups`
  ADD CONSTRAINT `user_id_refs_id_40c41112` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  ADD CONSTRAINT `group_id_refs_id_274b862c` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`);

--
-- Ограничения внешнего ключа таблицы `auth_user_user_permissions`
--
ALTER TABLE `auth_user_user_permissions`
  ADD CONSTRAINT `user_id_refs_id_4dc23c39` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  ADD CONSTRAINT `permission_id_refs_id_35d9ac25` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`);

--
-- Ограничения внешнего ключа таблицы `django_admin_log`
--
ALTER TABLE `django_admin_log`
  ADD CONSTRAINT `content_type_id_refs_id_93d2d1f8` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  ADD CONSTRAINT `user_id_refs_id_c0d12874` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

--
-- Ограничения внешнего ключа таблицы `djcelery_periodictask`
--
ALTER TABLE `djcelery_periodictask`
  ADD CONSTRAINT `crontab_id_refs_id_286da0d1` FOREIGN KEY (`crontab_id`) REFERENCES `djcelery_crontabschedule` (`id`),
  ADD CONSTRAINT `interval_id_refs_id_1829f358` FOREIGN KEY (`interval_id`) REFERENCES `djcelery_intervalschedule` (`id`);

--
-- Ограничения внешнего ключа таблицы `djcelery_taskstate`
--
ALTER TABLE `djcelery_taskstate`
  ADD CONSTRAINT `worker_id_refs_id_6fd8ce95` FOREIGN KEY (`worker_id`) REFERENCES `djcelery_workerstate` (`id`);

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
