package com.happy.travian.repository;

import com.happy.travian.domain.TroopCount;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface TroopCountRepository extends JpaRepository<TroopCount, Long> {
  List<TroopCount> findByVillageId(Long villageId);
}