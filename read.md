# E-Learning Platform Analytics API

## Overview
FastAPI backend for an e-learning platform to manage courses, track student progress, and provide analytics. Features include:

- JWT authentication with role-based access
- MongoDB for data storage and Redis for caching
- Real-time dashboards and analytics
- Course management with modules, lessons, quizzes
- Progress tracking and learning insights

---

## Features

### Authentication
- Login, register, refresh, logout
- Redis session management and token blacklisting

### Courses
- CRUD operations with file uploads
- Categorization, tagging, and caching
- Course analytics endpoints for instructors

### Progress Tracking
- Lesson completion, quiz scores, and time tracking
- Dashboard views and progress caching

### Analytics
- Course performance and learning patterns
- Platform overview for admins
- Cached analytics results

### Caching
- Multi-level Redis caching (courses, progress, analytics)
- Cache invalidation on updates
- Background cache warming

---

## Technical Stack
- **Backend:** FastAPI, Pydantic
- **Database:** MongoDB (PyMongo, connection pooling)
- **Cache:** Redis (sessions, data, analytics)
- **Auth:** JWT with role-based access
- **Background Tasks:** FastAPI BackgroundTasks / APScheduler

---

## Key Endpoints

**Auth**
- `POST /auth/login` | `POST /auth/register`
- `POST /auth/refresh` | `DELETE /auth/logout`

**Courses**
- `GET /courses` | `POST /courses`
- `GET /courses/{id}` | `PUT /courses/{id}/modules/{module_id}`
- `GET /courses/{id}/analytics`

**Progress**
- `POST /progress/lessons/{lesson_id}/complete`
- `GET /progress/dashboard`
- `GET /progress/courses/{course_id}`

**Analytics**
- `GET /analytics/courses/{course_id}/performance`
- `GET /analytics/students/{student_id}/learning-patterns`
- `GET /analytics/platform/overview`

**Cache**
- `DELETE /cache/courses/{course_id}`
- `GET /cache/stats`

---

## Setup

```bash
git clone <repo-url>
cd e-learning-platform
pip install -r requirements.txt
