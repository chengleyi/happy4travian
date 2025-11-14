package com.happy.travian.repository;

import com.happy.travian.domain.Server;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;

public interface ServerRepository extends JpaRepository<Server, Long> {
  Optional<Server> findByCode(String code);
}