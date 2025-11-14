package com.happy.travian.repository;

import com.happy.travian.domain.Village;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface VillageRepository extends JpaRepository<Village, Long> {
  List<Village> findByServerId(Long serverId);
  List<Village> findByGameAccountId(Long gameAccountId);
}