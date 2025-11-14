package com.happy.travian.repository;

import com.happy.travian.domain.TroopType;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface TroopTypeRepository extends JpaRepository<TroopType, Integer> {
  List<TroopType> findByTribeId(Integer tribeId);
}