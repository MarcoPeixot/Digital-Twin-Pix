package br.ufrj.cos.twin.processingcore;

import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.Gauge;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;
import java.util.concurrent.Semaphore;
import java.util.concurrent.ThreadLocalRandom;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

@RestController
public class TransactionController {

    private static final Logger log = LoggerFactory.getLogger(TransactionController.class);

    private final TransactionRepository repository;
    private final Timer processingTimer;
    private final Counter processingSuccessCounter;
    private final Counter processingErrorCounter;
    private final Counter processingTimeoutCounter;
    private final Counter processingQueueRejectionCounter;
    private final Timer queueWaitTimer;
    private final ProcessingExperimentSettings experimentSettings;
    private final Semaphore workerSemaphore;
    private final AtomicInteger queueDepth = new AtomicInteger(0);
    private final AtomicInteger backlogMax = new AtomicInteger(0);
    private final AtomicInteger activeWorkers = new AtomicInteger(0);

    public TransactionController(
            TransactionRepository repository,
            MeterRegistry meterRegistry,
            ProcessingExperimentSettings experimentSettings
    ) {
        this.repository = repository;
        this.experimentSettings = experimentSettings;
        this.workerSemaphore = new Semaphore(experimentSettings.workerCount(), true);
        this.processingTimer = Timer.builder("twinpix_processing_duration_seconds")
                .description("Transaction processing latency")
                .publishPercentiles(0.5, 0.95, 0.99)
                .register(meterRegistry);
        this.processingSuccessCounter = Counter.builder("twinpix_processing_total")
                .tag("status", "success")
                .description("Total transactions processed")
                .register(meterRegistry);
        this.processingErrorCounter = Counter.builder("twinpix_processing_total")
                .tag("status", "error")
                .description("Total transactions processed")
                .register(meterRegistry);
        this.processingTimeoutCounter = Counter.builder("twinpix_processing_timeouts_total")
                .description("Total queue wait timeouts")
                .register(meterRegistry);
        this.processingQueueRejectionCounter = Counter.builder("twinpix_processing_queue_rejections_total")
                .description("Total queue rejections")
                .register(meterRegistry);
        this.queueWaitTimer = Timer.builder("twinpix_processing_queue_wait_seconds")
                .description("Time spent waiting for processing worker")
                .publishPercentiles(0.5, 0.95, 0.99)
                .register(meterRegistry);

        Gauge.builder("twinpix_processing_queue_depth", queueDepth, AtomicInteger::get)
                .description("Current queue depth")
                .register(meterRegistry);
        Gauge.builder("twinpix_processing_backlog_max", backlogMax, AtomicInteger::get)
                .description("Maximum backlog observed")
                .register(meterRegistry);
        Gauge.builder("twinpix_processing_active_workers", activeWorkers, AtomicInteger::get)
                .description("Current active workers")
                .register(meterRegistry);
        Gauge.builder("twinpix_processing_worker_capacity", experimentSettings, ProcessingExperimentSettings::workerCount)
                .description("Configured worker capacity")
                .register(meterRegistry);
    }

    @PostMapping("/transactions/process")
    public ResponseEntity<?> process(@RequestBody ProcessRequest request) {
        log.info("Processing transaction: {} -> {} amount={}", request.sourceKey(), request.destinationKey(), request.amount());

        if (request.sourceKey() == null || request.sourceKey().isBlank()) {
            return ResponseEntity.badRequest().body(Map.of("error", "sourceKey is required"));
        }
        if (request.destinationKey() == null || request.destinationKey().isBlank()) {
            return ResponseEntity.badRequest().body(Map.of("error", "destinationKey is required"));
        }
        if (request.destinationName() == null || request.destinationName().isBlank()) {
            return ResponseEntity.badRequest().body(Map.of("error", "destinationName is required"));
        }
        if (request.amount() == null || request.amount().signum() <= 0) {
            return ResponseEntity.badRequest().body(Map.of("error", "amount must be positive"));
        }

        Timer.Sample sample = Timer.start();
        boolean permitAcquired = false;
        boolean queued = false;
        long waitStartNanos = System.nanoTime();

        Transaction tx = new Transaction(
                request.sourceKey(),
                request.destinationKey(),
                request.destinationName(),
                request.amount()
        );

        try {
            if (workerSemaphore.tryAcquire()) {
                permitAcquired = true;
            } else {
                int currentQueueDepth = queueDepth.incrementAndGet();
                queued = true;
                updateBacklogMax(currentQueueDepth);

                if (currentQueueDepth > experimentSettings.queueCapacity()) {
                    queueDepth.decrementAndGet();
                    processingQueueRejectionCounter.increment();
                    processingErrorCounter.increment();
                    sample.stop(processingTimer);
                    log.warn("Queue rejected request due to capacity limit");
                    return ResponseEntity.status(503).body(Map.of("error", "processing queue saturated"));
                }

                permitAcquired = workerSemaphore.tryAcquire(
                        experimentSettings.queueWaitTimeoutMs(),
                        TimeUnit.MILLISECONDS
                );

                queueWaitTimer.record(System.nanoTime() - waitStartNanos, TimeUnit.NANOSECONDS);
                queueDepth.decrementAndGet();
                queued = false;

                if (!permitAcquired) {
                    processingTimeoutCounter.increment();
                    processingErrorCounter.increment();
                    sample.stop(processingTimer);
                    log.warn("Queue wait timeout after {}ms", experimentSettings.queueWaitTimeoutMs());
                    return ResponseEntity.status(503).body(Map.of("error", "processing timeout"));
                }
            }

            activeWorkers.incrementAndGet();
            simulateProcessingDelay();

            if (shouldForceError()) {
                processingErrorCounter.increment();
                sample.stop(processingTimer);
                log.warn("Forced processing error for transaction request");
                return ResponseEntity.internalServerError().body(Map.of("error", "processing failed"));
            }

            tx = repository.save(tx);

            long elapsed = System.currentTimeMillis() - tx.getCreatedAt().toEpochMilli();
            tx.markCompleted(elapsed);
            tx = repository.save(tx);

            sample.stop(processingTimer);
            processingSuccessCounter.increment();

            log.info("Transaction {} completed in {}ms", tx.getId(), elapsed);

            return ResponseEntity.ok(new ProcessResponse(
                    tx.getId(),
                    tx.getStatus(),
                    tx.getProcessingTimeMs(),
                    tx.getCreatedAt()
            ));
        } catch (Exception e) {
            sample.stop(processingTimer);
            processingErrorCounter.increment();
            log.error("Transaction processing failed", e);
            return ResponseEntity.internalServerError().body(Map.of("error", "processing failed"));
        } finally {
            if (queued) {
                queueDepth.decrementAndGet();
            }
            if (permitAcquired) {
                activeWorkers.updateAndGet(current -> Math.max(0, current - 1));
                workerSemaphore.release();
            }
        }
    }

    private void simulateProcessingDelay() {
        long delayMs = experimentSettings.processingDelayMs();
        if (experimentSettings.processingDelayJitterMs() > 0) {
            delayMs += ThreadLocalRandom.current().nextLong(experimentSettings.processingDelayJitterMs() + 1L);
        }

        if (delayMs <= 0) {
            return;
        }

        try {
            Thread.sleep(delayMs);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            log.warn("Processing delay simulation interrupted");
        }
    }

    private boolean shouldForceError() {
        return experimentSettings.errorRate() > 0.0
                && ThreadLocalRandom.current().nextDouble() < experimentSettings.errorRate();
    }

    private void updateBacklogMax(int candidate) {
        backlogMax.accumulateAndGet(candidate, Math::max);
    }
}
