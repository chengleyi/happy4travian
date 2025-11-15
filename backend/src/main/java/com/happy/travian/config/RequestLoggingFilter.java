package com.happy.travian.config;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

@Component
public class RequestLoggingFilter extends OncePerRequestFilter {
  private static final Logger log = LoggerFactory.getLogger(RequestLoggingFilter.class);

  @Override
  protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain) throws ServletException, IOException {
    long start = System.currentTimeMillis();
    String method = request.getMethod();
    String uri = request.getRequestURI();
    String qs = request.getQueryString();
    filterChain.doFilter(request, response);
    long cost = System.currentTimeMillis() - start;
    int status = response.getStatus();
    String path = qs == null ? uri : uri + "?" + qs;
    log.info("api {} {} status={} cost={}ms", method, path, status, cost);
  }
}