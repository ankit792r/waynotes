package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"syscall"
	"time"
)

type Todo struct {
	ID        string    `json:"id"`
	Title     string    `json:"title"`
	Completed bool      `json:"completed"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

type Store struct {
	mu    sync.RWMutex
	todos map[string]Todo
	next  uint64
}

func NewStore() *Store {
	return &Store{
		todos: make(map[string]Todo),
	}
}
func (s *Store) List() []Todo {
	s.mu.RLock()
	defer s.mu.RUnlock()

	result := make([]Todo, 0, len(s.todos))
	for _, todo := range s.todos {
		result = append(result, todo)
	}

	sort.Slice(result, func(i, j int) bool {
		return result[i].CreatedAt.Before(result[j].CreatedAt)
	})

	return result
}

func (s *Store) Count() (pending, completed, total int) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	total = len(s.todos)
	for _, todo := range s.todos {
		if todo.Completed {
			completed++
		} else {
			pending++
		}
	}
	return
}

func (s *Store) Create(title string) Todo {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.next++
	now := time.Now().UTC()

	todo := Todo{
		ID:        fmt.Sprintf("%d-%d", now.UnixNano(), s.next),
		Title:     title,
		Completed: false,
		CreatedAt: now,
		UpdatedAt: now,
	}

	s.todos[todo.ID] = todo
	return todo
}

func (s *Store) Get(id string) (Todo, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	todo, ok := s.todos[id]
	return todo, ok
}

func (s *Store) Update(
	id string,
	title *string,
	completed *bool,
) (Todo, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()

	todo, ok := s.todos[id]
	if !ok {
		return Todo{}, false
	}

	if title != nil {
		todo.Title = *title
	}
	if completed != nil {
		todo.Completed = *completed
	}

	todo.UpdatedAt = time.Now().UTC()
	s.todos[id] = todo

	return todo, true
}

func (s *Store) Delete(id string) bool {
	s.mu.Lock()
	defer s.mu.Unlock()

	if _, ok := s.todos[id]; !ok {
		return false
	}

	delete(s.todos, id)
	return true
}

type Server struct {
	store *Store
}

func NewServer() *Server {
	return &Server{store: NewStore()}
}

func (s *Server) routes() http.Handler {
	mux := http.NewServeMux()

	mux.HandleFunc("GET /api/v1/health", s.health)
	mux.HandleFunc("GET /api/v1/todos/count", s.count)
	mux.HandleFunc("GET /api/v1/todos", s.list)
	mux.HandleFunc("POST /api/v1/todos", s.create)
	mux.HandleFunc("GET /api/v1/todos/{id}", s.get)
	mux.HandleFunc("PATCH /api/v1/todos/{id}", s.update)
	mux.HandleFunc("DELETE /api/v1/todos/{id}", s.delete)

	return mux
}

func writeJSON(w http.ResponseWriter, status int, value any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.Header().Set("Cache-Control", "no-store")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(value)
}

func writeError(w http.ResponseWriter, status int, message string) {
	writeJSON(w, status, map[string]string{"error": message})
}

func decodeJSON(w http.ResponseWriter, r *http.Request, dst any) error {
	r.Body = http.MaxBytesReader(w, r.Body, 1<<20)

	decoder := json.NewDecoder(r.Body)
	decoder.DisallowUnknownFields()

	if err := decoder.Decode(dst); err != nil {
		return err
	}

	var extra any
	if err := decoder.Decode(&extra); err != io.EOF {
		if err == nil {
			return errors.New("request must contain one JSON value")
		}
		return err
	}

	return nil
}

func (s *Server) health(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

func (s *Server) count(w http.ResponseWriter, r *http.Request) {
	pending, completed, total := s.store.Count()
	writeJSON(w, http.StatusOK, map[string]int{
		"pending":   pending,
		"completed": completed,
		"total":     total,
	})
}

func (s *Server) list(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, map[string]any{
		"todos": s.store.List(),
	})
}

func (s *Server) get(w http.ResponseWriter, r *http.Request) {
	todo, ok := s.store.Get(r.PathValue("id"))
	if !ok {
		writeError(w, http.StatusNotFound, "todo not found")
		return
	}

	writeJSON(w, http.StatusOK, todo)
}

func (s *Server) create(w http.ResponseWriter, r *http.Request) {
	var input struct {
		Title string `json:"title"`
	}

	if err := decodeJSON(w, r, &input); err != nil {
		writeError(w, http.StatusBadRequest, "invalid JSON body")
		return
	}

	title := strings.TrimSpace(input.Title)
	if title == "" {
		writeError(w, http.StatusBadRequest, "title is required")
		return
	}
	if len(title) > 500 {
		writeError(w, http.StatusBadRequest, "title is too long (max 500 bytes)")
		return
	}

	todo := s.store.Create(title)
	writeJSON(w, http.StatusCreated, todo)
}

func (s *Server) update(w http.ResponseWriter, r *http.Request) {
	var input struct {
		Title     *string `json:"title"`
		Completed *bool   `json:"completed"`
	}

	if err := decodeJSON(w, r, &input); err != nil {
		writeError(w, http.StatusBadRequest, "invalid JSON body")
		return
	}

	if input.Title == nil && input.Completed == nil {
		writeError(w, http.StatusBadRequest, "no fields to update")
		return
	}

	if input.Title != nil {
		title := strings.TrimSpace(*input.Title)
		if title == "" {
			writeError(w, http.StatusBadRequest, "title cannot be empty")
			return
		}
		if len(title) > 500 {
			writeError(w, http.StatusBadRequest, "title is too long (max 500 bytes)")
			return
		}
		input.Title = &title
	}

	todo, ok := s.store.Update(
		r.PathValue("id"),
		input.Title,
		input.Completed,
	)
	if !ok {
		writeError(w, http.StatusNotFound, "todo not found")
		return
	}

	writeJSON(w, http.StatusOK, todo)
}

func (s *Server) delete(w http.ResponseWriter, r *http.Request) {
	if !s.store.Delete(r.PathValue("id")) {
		writeError(w, http.StatusNotFound, "todo not found")
		return
	}

	w.WriteHeader(http.StatusNoContent)
}

func socketPath() (string, error) {
	runtimeDir := os.Getenv("XDG_RUNTIME_DIR")
	if runtimeDir == "" {
		return "", errors.New("XDG_RUNTIME_DIR is not set")
	}
	if !filepath.IsAbs(runtimeDir) {
		return "", errors.New("XDG_RUNTIME_DIR must be an absolute path")
	}

	info, err := os.Stat(runtimeDir)
	if err != nil {
		return "", fmt.Errorf("inspect runtime directory: %w", err)
	}
	if !info.IsDir() {
		return "", errors.New("XDG_RUNTIME_DIR is not a directory")
	}
	if info.Mode().Perm()&0077 != 0 {
		return "", errors.New("XDG_RUNTIME_DIR must not be accessible by group or others")
	}

	return filepath.Join(runtimeDir, "waynotes-daemon.sock"), nil
}

func listenUnix(path string) (net.Listener, error) {
	// Never remove a path unless it is an actual socket.
	if info, err := os.Lstat(path); err == nil {
		if info.Mode()&os.ModeSocket == 0 {
			return nil, fmt.Errorf("refusing to remove non-socket path: %s", path)
		}

		// Probe for an existing server before cleaning up a stale socket.
		conn, dialErr := net.DialTimeout("unix", path, 300*time.Millisecond)
		if dialErr == nil {
			conn.Close()
			return nil, errors.New("another todo daemon appears to be running")
		}

		if err := os.Remove(path); err != nil {
			return nil, fmt.Errorf("remove stale socket: %w", err)
		}
	} else if !os.IsNotExist(err) {
		return nil, fmt.Errorf("inspect socket path: %w", err)
	}

	listener, err := net.Listen("unix", path)
	if err != nil {
		return nil, fmt.Errorf("listen on Unix socket: %w", err)
	}

	// Only the owning user can access the socket.
	if err := os.Chmod(path, 0600); err != nil {
		listener.Close()
		os.Remove(path)
		return nil, fmt.Errorf("secure socket permissions: %w", err)
	}

	return listener, nil
}

func run() error {
	path, err := socketPath()
	if err != nil {
		return err
	}

	listener, err := listenUnix(path)
	if err != nil {
		return err
	}

	// Remove our socket when the listener closes.
	defer func() {
		listener.Close()
		os.Remove(path)
	}()

	server := &http.Server{
		Handler:           NewServer().routes(),
		ReadHeaderTimeout: 5 * time.Second,
		ReadTimeout:       10 * time.Second,
		WriteTimeout:      10 * time.Second,
		IdleTimeout:       60 * time.Second,
	}

	ctx, stop := signal.NotifyContext(
		context.Background(),
		os.Interrupt,
		syscall.SIGTERM,
	)
	defer stop()

	errCh := make(chan error, 1)
	go func() {
		log.Printf("todo daemon listening on %s", path)
		errCh <- server.Serve(listener)
	}()

	select {
	case <-ctx.Done():
		shutdownCtx, cancel := context.WithTimeout(
			context.Background(), 5*time.Second,
		)
		defer cancel()
		return server.Shutdown(shutdownCtx)

	case err := <-errCh:
		if errors.Is(err, http.ErrServerClosed) {
			return nil
		}
		return err
	}
}

func main() {
	if err := run(); err != nil {
		log.Fatal(err)
	}
}
