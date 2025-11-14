package com.happy.travian.repository;

import com.happy.travian.domain.Alliance;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface AllianceRepository extends JpaRepository<Alliance, Long> {
  List<Alliance> findByServerId(Long serverId);
}